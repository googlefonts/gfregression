import re
import os
from glob import glob
import shutil
import requests
from urllib import urlopen
from zipfile import ZipFile
from StringIO import StringIO
import ntpath
from fontTools.ttLib import TTFont
from collections import namedtuple

FONT_EXCEPTIONS = {
    'VT323': 'VT323',
    'AmaticSC': 'Amatic SC',
    'AmaticaSC': 'Amatica SC',
    'OldStandardTT': 'Old Standard TT',
}


def unify_font_sets(fonts1, fonts2):
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


def upload_fonts(request, ajax_key, fonts_path):
    """Upload the fonts from a request to a specified path"""
    os.mkdir(fonts_path)

    for upload in request.files.getlist(ajax_key):
        filename = upload.filename.rsplit("/")[0]
        destination = "/".join([fonts_path, filename])
        upload.save(destination)


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










def _convert_camelcase(fam_name, seperator=' '):
    '''RubikMonoOne > Rubik+Mono+One'''
    if fam_name not in FONT_EXCEPTIONS:
        return re.sub('(?!^)([A-Z]|[0-9]+)', r'%s\1' % seperator, fam_name)
    else:
        fam_name = FONT_EXCEPTIONS[fam_name].replace(' ', seperator)
        return fam_name


def gf_download_url(fontspath):
    """Assemble download url for families"""
    gf_url_prefix = 'https://fonts.google.com/download?family='
    families_name = set([_convert_camelcase(f.split('-')[0], '%20')
                        for f in fontspath if f.endswith('.ttf')])
    families_url_suffix = '|'.join(families_name)
    return gf_url_prefix + families_url_suffix


def download_fonts(url, to_dir):
    """Return a zipfile containing a font family hosted on fonts.google.com"""
    request = urlopen(url)
    if request.getcode() == 200:
        fonts_zip = ZipFile(StringIO(request.read()))
        fonts_from_zip(fonts_zip, to_dir)
    else:
        return 'Url does not contain fonts'


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


def delete_fonts(path):
    """Delete any ttfs in a specific folder"""
    for item in os.listdir(path):
        if os.path.isdir(os.path.join(path, item)):
            shutil.rmtree(os.path.join(path, item))
        else:
            if item.endswith('.ttf'):
                os.remove(os.path.join(path, item))
