import re
import os
from glob import glob
import shutil
import requests
from urllib import urlopen
import ntpath
from StringIO import StringIO
from fontTools.ttLib import TTFont
from collections import namedtuple
import json


Font = namedtuple('Font', [
    'path', 'csspath', 'fullname', 'css_name', 'css_style', 'css_class', 'css_weight', 'font',
    # OS/2 typo attributes
    'sTypoAscender', 'sTypoDescender', 'sTypoLineGap',
    # OS/2 win attributes
    'usWinAscent', 'usWinDescent',
    # hhea attributes
    'hheaAscender', 'hheaDescender', 'hheaLineGap',
    # glyph counts
    'glyph_count', 'glyph_encoded_count',
])

CSS_WEIGHT = {
    'Thin': 100,
    'ExtraLight': 200,
    'Light': 300,
    'Regular': 400,
    '': 400,
    'Medium': 500,
    'SemiBold': 600,
    'Bold': 700,
    'ExtraBold': 800,
    'Black': 900,

}

def gfr_font(path, suffix):
    """High level wrapper for TTFont object which contains additional
    properties for html/css manipulation"""

    font = TTFont(path)
    name = ntpath.basename(path)[:-4]
    family_name = name.split('-')[0]
    weight = name.split('-')[1].replace('Italic', '')

    css_class = '%s-%s' % (name, suffix)
    css_name = '%s-%s' % (family_name, suffix)
    css_style = 'italic' if 'Italic' in name else 'normal'
    css_weight = CSS_WEIGHT[weight] if weight in CSS_WEIGHT else 400

    return Font(
        path=path,
        csspath = '/' + path,
        fullname=name,
        css_name=css_name,
        css_style=css_style,
        css_class=css_class,
        css_weight=css_weight,
        font=font,
        sTypoAscender=font['OS/2'].sTypoAscender,
        sTypoDescender=font['OS/2'].sTypoDescender,
        sTypoLineGap=font['OS/2'].sTypoLineGap,
        usWinAscent=font['OS/2'].usWinAscent,
        usWinDescent=font['OS/2'].usWinDescent,
        hheaAscender=font['hhea'].ascent,
        hheaDescender=font['hhea'].descent,
        hheaLineGap=font['hhea'].lineGap,
        glyph_count=len(font.getGlyphSet().keys()),
        glyph_encoded_count=len(font['cmap'].getcmap(3, 1).cmap.keys()),

    )
