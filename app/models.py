from peewee import (
    SqliteDatabase,
    Model,
    CharField,
    IntegerField,
    TextField,
    )

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


db = SqliteDatabase('iso639corpora.db')


class Languages(Model):
    name = CharField()
    part1 = CharField(null=True)
    part2 = CharField(null=True)
    part3 = CharField(null=True)
    wiki_id = IntegerField(null=True)
    text = TextField(null=True)

    class Meta:
        database = db


def gfr_font(path, fullname, cssname, font):
    """High level wrapper for TTFont object which contains additional
    properties for css manipulation"""
    Font = namedtuple('Font', [
        'path', 'csspath', 'fullname', 'cssname', 'font',
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
        path=path,
        csspath = '/' + path,
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
