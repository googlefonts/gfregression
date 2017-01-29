'''
Compare local fonts against fonts available on fonts.google.com
'''
from __future__ import print_function
from flask import Flask, render_template
from fontTools.ttLib import TTFont
from fontTools.pens.areaPen import AreaPen
from glob import glob
import ntpath
import requests
import re
import os
import atexit
import shutil
from urllib import urlopen
from zipfile import ZipFile
from StringIO import StringIO

URL_PREFIX = 'https://fonts.google.com/download?family='

FONT_EXCEPTIONS = [
    'VT323',
    'Amatic SC',
    'Amatica SC',
]

LOCAL_FONTS_PATH = './static/'
REMOTE_FONTS_PATH = './static/remotefonts/'

app = Flask(__name__)

with open('./dummy_text.txt', 'r') as dummy_text_file:
    dummy_text = dummy_text_file.read()


def _url_200_response(url):
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
        _unnest_dir(to)


def _unnest_dir(dir):
    for r, path, files, in os.walk(dir):
        for file in files:
            if file.endswith('.ttf'):
                shutil.move(os.path.join(r, file), dir)

    for f in os.listdir(dir):
        if os.path.isdir(os.path.join(dir, f)):
            os.rmdir(os.path.join(dir, f))


def font_glyphs(local_fonts):
    """return encoded glyphs for each font"""
    glyphs = {}

    for path, font, span_name in local_fonts:
        ttfont = TTFont(path)
        glyphs[font] = []

        cmap_tbl = ttfont['cmap'].getcmap(3, 1)
        glyphs[font] = cmap_tbl.cmap.items()
    return glyphs


def css_properties(paths, suffix):
    """Create the properties needed to load @fontface fonts"""
    fonts = []
    for path in paths:
        path = path.replace('\\', '/')
        name = ntpath.basename(path)[:-4]
        font_name = '%s-%s' % (name, suffix)
        span_name = '%s-%s' % (ntpath.basename(path)[:-4], suffix)
        fonts.append((path, name, font_name, span_name))
    return fonts


def pad(coll1, coll2):
    coll1_names = [n[1].lower() for n in coll1]
    coll2_names = [n[1].lower() for n in coll2]

    pos = 0
    for path, name, font_name, span_name in coll1:
        if name.lower() not in coll2_names:
            print('did not fine %s' % name)
            placeholder = ('NULL', name, 'NULL', 'NULL')
            coll2.insert(pos, placeholder)
        pos += 1
    # Return only the items available in coll1
    return [i for i in coll2 if i[1].lower() in coll1_names]


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
    local_fonts = sorted(local_fonts, key=lambda x: x[1])

    # Assemble download url for families
    remote_families_name = set([_convert_camelcase(f[1].split('-')[0], '%20')
                               for f in local_fonts])
    remote_families_url_suffix = '|'.join(remote_families_name)
    remote_families_url = URL_PREFIX + remote_families_url_suffix

    # download last fonts from fonts.google.com
    remote_fonts_zip = download_family_from_gf(remote_families_url)
    fonts_from_zip(remote_fonts_zip, REMOTE_FONTS_PATH)

    remote_fonts_paths = glob(REMOTE_FONTS_PATH + '*.ttf')
    remote_fonts = css_properties(remote_fonts_paths, 'old')
    pad_remote_fonts = pad(local_fonts, remote_fonts)
    remote_fonts = sorted(pad_remote_fonts, key=lambda x: x[1])

    # char_maps = font_glyphs(local_fonts)
    to_local_fonts = ','.join([i[2] for i in local_fonts])
    to_remote_fonts = ','.join([i[2] for i in remote_fonts])

    return render_template(
        'index.html',
        dummy_text=dummy_text,
        local_fonts=local_fonts,
        remote_fonts=remote_fonts,
        # char_maps=char_maps,
        to_local_fonts=to_local_fonts,
        to_google_fonts=to_remote_fonts
    )


if __name__ == "__main__":
    app.config['STATIC_FOLDER'] = 'static'
    app.run(debug=True)
    atexit.register(_delete_remote_fonts)
