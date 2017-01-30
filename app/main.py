'''
Compare local fonts against fonts available on fonts.google.com
'''
from __future__ import print_function
from flask import Flask, render_template
from fontTools.ttLib import TTFont
from fontTools.pens.areaPen import AreaPen
from glob import glob
from collections import namedtuple
import ntpath
import requests
import re
import os
import atexit
import shutil
from urllib import urlopen
from zipfile import ZipFile
from StringIO import StringIO
from pprint import pprint

URL_PREFIX = 'https://fonts.google.com/download?family='

FONT_EXCEPTIONS = [
    'VT323',
    'Amatic SC',
    'Amatica SC',
]

LOCAL_FONTS_PATH = './static/'
REMOTE_FONTS_PATH = './static/remotefonts/'


GLYPH_THRESHOLD = 8000

app = Flask(__name__)

with open('./dummy_text.txt', 'r') as dummy_text_file:
    dummy_text = dummy_text_file.read()


def url_200_response(url):
    '''Check if the url mataches the Google fonts api url'''
    if requests.get(url).status_code == 200:
        return True
    return False


def _convert_camelcase(fam_name, seperator=' '):
    '''RubikMonoOne > Rubik+Mono+One'''
    if fam_name not in FONT_EXCEPTIONS:
        return re.sub('(?!^)([A-Z]|[0-9]+)', r'%s\1' % seperator, fam_name)
    else:
        return fam_name


def gf_download_url(local_fonts):
    """Assemble download url for families"""
    remote_families_name = set([_convert_camelcase(f.split('-')[0], '%20')
                               for f in local_fonts])
    remote_families_url_suffix = '|'.join(remote_families_name)
    return URL_PREFIX + remote_families_url_suffix


def download_family_from_gf(url):
    """Return a zipfile containing a font family hosted on fonts.google.com"""
    request = urlopen(url)
    return ZipFile(StringIO(request.read()))


def fonts_from_zip(zipfile, to):
    """download the fonts and store them locally"""
    unnest = False
    for file_name in zipfile.namelist():
        if file_name.endswith(".ttf"):
            zipfile.extract(file_name, to)
        if '/' in file_name:
            unnest = True
    if unnest:
        _unnest_folder(to)


def _unnest_folder(folder):
    """If multiple fonts have been downloaded, move them from sub dirs to
    parent dir"""
    for r, path, files, in os.walk(folder):
        for file in files:
            if file.endswith('.ttf'):
                shutil.move(os.path.join(r, file), folder)

    for f in os.listdir(folder):
        if os.path.isdir(os.path.join(folder, f)):
            os.rmdir(os.path.join(folder, f))


def css_properties(paths, suffix):
    """Create a collection of css_property objects"""
    fonts = []
    for path in paths:
        name = ntpath.basename(path)[:-4]
        font = css_property(
            path=path.replace('\\', '/'),
            fullname=name,
            cssname='%s-%s' % (name, suffix),
        )
        fonts.append(font)
    return fonts


def css_property(path, fullname, cssname):
    """Create the properties needed to load @fontface fonts"""
    Font = namedtuple('Font', ['path', 'fullname', 'cssname'])
    name = ntpath.basename(path)[:-4]
    font = Font(
        path=path,
        fullname=fullname,
        cssname=cssname,
    )
    return font


def inconsistent_glyphs(local_fonts, remote_fonts, names):
    """return glyphs which have changed from local to remote"""
    glyphs = {}
    bad_glyphs = {}
    for l_font, r_font, name in zip(local_fonts, remote_fonts, names):
        l_glyphs = l_font['glyf'].glyphs.keys()
        r_glyphs = r_font['glyf'].glyphs.keys()
        shared_glyphs = set(l_glyphs) & set(r_glyphs)

        l_glyphs = l_font.getGlyphSet()
        r_glyphs = r_font.getGlyphSet()

        l_pen = AreaPen(l_glyphs)
        r_pen = AreaPen(r_glyphs)

        for glyph in shared_glyphs:
            l_glyphs[glyph].draw(l_pen)
            r_glyphs[glyph].draw(r_pen)

            l_area = l_pen.value
            l_pen.value = 0
            r_area = r_pen.value
            r_pen.value = 0
            if l_area != r_area:
                if int(l_area) ^ int(r_area) > GLYPH_THRESHOLD:

                    if name not in bad_glyphs:
                        bad_glyphs[name] = []
                    bad_glyphs[name].append(glyph)

        l_cmap_tbl = l_font['cmap'].getcmap(3, 1).cmap
        glyphs[name] = [i for i in l_cmap_tbl.items() if i[1] in bad_glyphs[name]]
    return glyphs


def pad(coll1, coll2):
    coll1_names = [n.fullname.lower() for n in coll1]
    coll2_names = [n.fullname.lower() for n in coll2]

    pos = 0
    for font in coll1:
        if font.fullname.lower() not in coll2_names:
            print('did not fine %s' % font.fullname)
            placeholder = css_property(
                path='NULL',
                fullname=font.fullname,
                cssname='NULL',
            )
            coll2.insert(pos, placeholder)
        pos += 1
    # Return only the items available in coll1
    return [f for f in coll2 if f.fullname.lower() in coll1_names]


def _delete_remote_fonts():
    path = './static/remotefonts/'
    for file in os.listdir(path):
        if file.endswith('.ttf'):
            os.remove(os.path.join(path, file))


@app.route("/")
def test_fonts():
    # Clear fonts which may not have been deleted from previous session
    _delete_remote_fonts()

    local_fonts_paths = glob(LOCAL_FONTS_PATH + '*.ttf')
    local_fonts = css_properties(local_fonts_paths, 'new')
    local_fonts = sorted(local_fonts, key=lambda x: x.fullname)

    # Assemble download url for families
    remote_download_url = gf_download_url([i.fullname for i in local_fonts])
    # download last fonts from fonts.google.com
    if url_200_response(remote_download_url):
        remote_fonts_zip = download_family_from_gf(remote_download_url)

        fonts_from_zip(remote_fonts_zip, REMOTE_FONTS_PATH)

        remote_fonts_paths = glob(REMOTE_FONTS_PATH + '*.ttf')
        remote_fonts = css_properties(remote_fonts_paths, 'old')
    else:
        remote_fonts = []
    pad_remote_fonts = pad(local_fonts, remote_fonts)
    remote_fonts = sorted(pad_remote_fonts, key=lambda x: x.fullname)

    char_maps = inconsistent_glyphs(
        [TTFont(i.path) for i in local_fonts if i.path.endswith('.ttf')],
        [TTFont(i.path) for i in remote_fonts if i.path.endswith('.ttf')],
        [i.fullname for i in local_fonts],
    )
    print(pprint(char_maps))

    to_local_fonts = ','.join([i.cssname for i in local_fonts])
    to_remote_fonts = ','.join([i.cssname for i in remote_fonts])

    return render_template(
        'index.html',
        dummy_text=dummy_text,
        local_fonts=local_fonts,
        remote_fonts=remote_fonts,
        char_maps=char_maps,
        to_local_fonts=to_local_fonts,
        to_remote_fonts=to_remote_fonts
    )


if __name__ == "__main__":
    app.config['STATIC_FOLDER'] = 'static'
    app.run(debug=True)
    atexit.register(_delete_remote_fonts)
