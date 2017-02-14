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

__version__ = 0.200

URL_PREFIX = 'https://fonts.google.com/download?family='

FONT_EXCEPTIONS = [
    'VT323',
    'Amatic SC',
    'Amatica SC',
]

LOCAL_FONTS_PATH = './static/'
REMOTE_FONTS_PATH = './static/remotefonts/'

GLYPH_THRESHOLD = 0

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


def fonts(paths, suffix):
    """Create a collection of css_property objects"""
    fonts = []
    for path in paths:
        name = ntpath.basename(path)[:-4]
        font = css_property(
            path=path.replace('\\', '/'),
            fullname=name,
            cssname='%s-%s' % (name, suffix),
            font=TTFont(path)
        )
        fonts.append(font)
    return fonts


def css_property(path, fullname, cssname, font):
    """Create the properties needed to load @fontface fonts"""
    Font = namedtuple('Font', ['path', 'fullname', 'cssname', 'font'])
    name = ntpath.basename(path)[:-4]
    font = Font(
        path=path,
        fullname=fullname,
        cssname=cssname,
        font=font
    )
    return font


def inconsistent_fonts_glyphs(local_fonts, remote_fonts):
    """return glyphs which have changed from local to remote"""
    glyphs = {}
    bad_glyphs = {}

    for font in local_fonts:
        l_glyphs = local_fonts[font].font['glyf'].glyphs.keys()
        r_glyphs = remote_fonts[font].font['glyf'].glyphs.keys()
        shared_glyphs = set(l_glyphs) & set(r_glyphs)

        l_glyphs = local_fonts[font].font.getGlyphSet()
        r_glyphs = remote_fonts[font].font.getGlyphSet()

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

                    if font not in bad_glyphs:
                        bad_glyphs[font] = []
                    bad_glyphs[font].append(glyph)
                    print('Different %s' % glyph)

        l_cmap_tbl = local_fonts[font].font['cmap'].getcmap(3, 1).cmap
        try:
            glyphs[font] = [i for i in l_cmap_tbl.items() if i[1] in bad_glyphs[font]]
        except:
            print('%s has consistent glyphs' % font)
    return glyphs


def new_fonts_glyphs(local_fonts, remote_fonts):
    """Return glyphs which are new in local fonts"""
    glyphs = {}

    for font in local_fonts:
        l_glyphs = local_fonts[font].font['glyf'].glyphs.keys()
        r_glyphs = remote_fonts[font].font['glyf'].glyphs.keys()
        glyphs[font] = set(l_glyphs) - set(r_glyphs)

        l_cmap_tbl = local_fonts[font].font['cmap'].getcmap(3, 1).cmap
        r_cmap_tbl = remote_fonts[font].font['cmap'].getcmap(3, 1).cmap
        r_encoded_glyphs = [i[0] for i in r_cmap_tbl.items()]

        glyphs[font] = [i for i in l_cmap_tbl.items() if i[1] in glyphs[font] and
                        i[0] not in r_encoded_glyphs]
    return glyphs


def missing_fonts_glyphs(local_fonts, remote_fonts):
    """Return glyphs which are missing in local fonts"""
    glyphs = {}

    for font in local_fonts:
        l_glyphs = local_fonts[font].font['glyf'].glyphs.keys()
        r_glyphs = remote_fonts[font].font['glyf'].glyphs.keys()
        glyphs[font] = set(r_glyphs) - set(l_glyphs)

        l_cmap_tbl = local_fonts[font].font['cmap'].getcmap(3, 1).cmap
        l_encoded_glyphs = [i[0] for i in l_cmap_tbl.items()]
        r_cmap_tbl = remote_fonts[font].font['cmap'].getcmap(3, 1).cmap

        glyphs[font] = [i for i in r_cmap_tbl.items() if i[1] in glyphs[font] and
                        i[0] not in l_encoded_glyphs]
    return glyphs


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
    local_fonts = fonts(local_fonts_paths, 'new')

    # Assemble download url for families
    remote_download_url = gf_download_url([i.fullname for i in local_fonts])
    # download last fonts from fonts.google.com
    if url_200_response(remote_download_url):
        remote_fonts_zip = download_family_from_gf(remote_download_url)
        fonts_from_zip(remote_fonts_zip, REMOTE_FONTS_PATH)

        remote_fonts_paths = glob(REMOTE_FONTS_PATH + '*.ttf')
        remote_fonts = fonts(remote_fonts_paths, 'old')
    else:
        return 'Font is not hosted on fonts.google.com'

    shared_fonts = set([i.fullname for i in local_fonts]) & \
                   set([i.fullname for i in remote_fonts])

    local_fonts = {f.fullname: f for f in local_fonts
                   if f.fullname in shared_fonts}
    remote_fonts = {f.fullname: f for f in remote_fonts
                    if f.fullname in shared_fonts}

    changed_glyphs = inconsistent_fonts_glyphs(local_fonts, remote_fonts)
    new_glyphs = new_fonts_glyphs(local_fonts, remote_fonts)
    missing_glyphs = missing_fonts_glyphs(local_fonts, remote_fonts)

    to_local_fonts = ','.join([local_fonts[i].cssname for i in local_fonts])
    to_remote_fonts = ','.join([remote_fonts[i].cssname for i in remote_fonts])
    return render_template(
        'index.html',
        dummy_text=dummy_text,
        local_fonts=local_fonts.values(),
        remote_fonts=remote_fonts.values(),
        changed_glyphs=changed_glyphs,
        new_glyphs=new_glyphs,
        missing_glyphs=missing_glyphs,
        to_local_fonts=to_local_fonts,
        to_remote_fonts=to_remote_fonts
    )


if __name__ == "__main__":
    app.config['STATIC_FOLDER'] = 'static'
    app.run(debug=True)
    atexit.register(_delete_remote_fonts)
