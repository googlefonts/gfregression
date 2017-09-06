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


def equalize_font_sets(fonts1, fonts2):
    """Make sure each set has the same quantity and they are rearranged
    in alphabetical order by the fullname attribute"""
    shared_fonts = set([f.fullname for f in fonts1]) & \
                   set([f.fullname for f in fonts2])
    _keep_listed_fonts(shared_fonts, fonts1)
    _keep_listed_fonts(shared_fonts, fonts2)

    fonts1.sort(key=lambda x: x.fullname, reverse=True)
    fonts2.sort(key=lambda x: x.fullname, reverse=True)


def _keep_listed_fonts(store, l):
    for idx, item in enumerate(l):
        for idx, item in enumerate(l):
            if item.fullname not in store:
                l.pop(idx)


def get_fonts(path, ext):
    """Retrieve a collection of fonts from a url, zipped url or local
    collection of ttfs"""
    fonts_paths = glob(path + '/*.ttf')
    return fonts(fonts_paths, ext)


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
    Font = namedtuple('Font', [
        'path', 'fullname', 'cssname', 'font',
        # OS/2 typo attributes
        'sTypoAscender', 'sTypoDescender', 'sTypoLineGap',
        # OS/2 win attributes
        'usWinAscent', 'usWinDescent',
        # hhea attributes
        'hheaAscender', 'hheaDescender', 'hheaLineGap',
        # glyph counts
        'glyph_count', 'glyph_encoded_count',
    ])
    name = ntpath.basename(path)[:-4]
    font = Font(
        path=path[1:],
        fullname=fullname,
        cssname=cssname,
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
    return font


def download_file(url, dst_path=None):
    """Download a file from a url. If no url is specified, store the file
    as a StringIO object"""
    request = requests.get(url, stream=True)
    if not dst_path:
        return StringIO(request.content)
    with open(dst_path, 'wb') as downloaded_file:
        shutil.copyfileobj(request.raw, downloaded_file)


def delete_fonts(path):
    """Delete any ttfs in a specific folder"""
    for item in os.listdir(path):
        if os.path.isdir(os.path.join(path, item)):
            shutil.rmtree(os.path.join(path, item))
        else:
            if item.endswith('.ttf'):
                os.remove(os.path.join(path, item))
