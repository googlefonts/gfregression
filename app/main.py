'''
Compare local fonts against fonts available on fonts.google.com
'''
from __future__ import print_function
from flask import Flask, render_template
from fontTools.ttLib import TTFont
import glob
import ntpath
import requests
import re
import os
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

FONT_WEIGHTS = {
    # Roman
    'Thin': '100',
    'ExtraLight': '200',
    'Light': '300',
    'Regular': '400',
    'Medium': '500',
    'SemiBold': '600',
    'Bold': '700',
    'ExtraBold': '800',
    'Black': '900',
    # Italics
    'ThinItalic': '250i',
    'ExtraLightItalic': '275i',
    'LightItalic': '300i',
    'Italic': '400i',
    'MediumItalic': '500i',
    'SemiBoldItalic': '600i',
    'BoldItalic': '700i',
    'ExtraBoldItalic': '800i',
    'BlackItalic': '900i',
}

FONT_EXCEPTIONS = [
    'VT323'
]

FONT_FALLBACK = 'Inconsolata'

app = Flask(__name__)

with open('./dummy_text.txt', 'r') as dummy_text_file:
    dummy_text = dummy_text_file.read()

with open('./dummy_text_ru.txt', 'r') as dummy_text_ru_file:
    dummy_text_ru = dummy_text_ru_file.read()

with open('./dummy_text_vit.txt', 'r') as dummy_text_vit_file:
    dummy_text_vit = dummy_text_vit_file.read()


def _font_exists(url):
    '''Check if the url matches the Google fonts api url'''
    if requests.get(url).status_code == 200:
        return True
    return False


def _convert_camelcase(fam_name, separator=' '):
    '''RubikMonoOne > Rubik+Mono+One'''
    if fam_name not in FONT_EXCEPTIONS:
        return re.sub('(?!^)([A-Z]+)', r'%s\1' % separator, fam_name)
    else:
        return fam_name


def fonts_on_google(local_fonts):
    '''Find the local font on fonts.google.com, if not found
    return a fallback font'''
    fonts = []
    url_prefix = 'https://fonts.googleapis.com/css?family='
    fallback_font = url_prefix + FONT_FALLBACK

    for path, font, span_name in local_fonts:
        fam_name, style = font.split('-')

        api_fam_name = _convert_camelcase(fam_name, '+')
        css_fam_name = _convert_camelcase(fam_name)

        url = '%s%s:%s' % (url_prefix, api_fam_name, FONT_WEIGHTS[style])

        if _font_exists(url):
            if 'i' in FONT_WEIGHTS[style]:
                span_name = '%s-%s-italic-online' % (fam_name, FONT_WEIGHTS[style][:-1])

                fonts.append((fam_name,
                              css_fam_name,
                              span_name,
                              FONT_WEIGHTS[style][:-1],
                              'italic',
                              url))
            else:
                span_name = '%s-%s-normal-online' % (fam_name, FONT_WEIGHTS[style])
                fonts.append((fam_name,
                              css_fam_name,
                              span_name,
                              FONT_WEIGHTS[style],
                              'normal',
                              url))
        else:
            fonts.append(('Inconsolata',
                          'Inconsolata',
                          'Inconsolata-400-normal-online',
                          '400',
                          'normal',
                          fallback_font))
    return fonts


def font_glyphs(local_fonts):
    """return encoded glyphs for each font"""
    glyphs = {}

    for path, font, span_name in local_fonts:
        ttfont = TTFont(path)
        glyphs[font] = []

        cmap_tbl = ttfont['cmap'].getcmap(3, 1)
        glyphs[font] = cmap_tbl.cmap.items()
    return glyphs


@app.route("/")
def test_fonts():
    sep = os.path.sep
    # web browsers use unix slashes, instead of windows
    local_fonts = []
    ttfs_in_static = glob.glob("." + sep + "static" + sep + "*.ttf")
    for path in ttfs_in_static:
        path = path.replace('\\', '/')
        font_name = ntpath.basename(path)[:-4]
        span_name = '%s-new' % ntpath.basename(path)[:-4]
        local_fonts.append((path, font_name, span_name))

    local_fonts = sorted(local_fonts, key=lambda x: x[1])
    google_fonts = fonts_on_google(local_fonts)
    char_maps = font_glyphs(local_fonts)
    to_local_fonts = ','.join([i[2] for i in local_fonts])
    to_google_fonts = ','.join([i[2] for i in google_fonts])

    return render_template('index.html',
                           dummy_text=dummy_text,
                           dummy_text_ru=dummy_text_ru,
                           dummy_text_vit=dummy_text_vit,
                           local_fonts=local_fonts,
                           google_fonts=google_fonts,
                           char_maps=char_maps,
                           to_local_fonts=to_local_fonts,
                           to_google_fonts=to_google_fonts)


if __name__ == "__main__":
    app.config['STATIC_FOLDER'] = 'static'
    app.run(debug=True)
