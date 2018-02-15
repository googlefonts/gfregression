"""
Module for retrieving fonts
"""
import json
import requests
import os
import re
from zipfile import ZipFile
from StringIO import StringIO
import shutil

from utils import download_file, secret
from blacklist import FONT_EXCEPTIONS
from settings import FONTS_DIR


def google_fonts(families):
    """Download a collection of font families from Google Fonts"""
    googlefonts_has_families(families)
    url = _gf_download_url(families)
    fonts_zip = ZipFile(download_file(url))
    fonts = fonts_from_zip(fonts_zip, FONTS_DIR)
    return fonts


def googlefonts_has_families(families):
    """Check if Google Fonts has the specified font family"""
    api_url = 'https://www.googleapis.com/webfonts/v1/webfonts?key={}'.format(
        secret('GF_API_KEY')
    )
    r = requests.get(api_url)
    families_on_gf = [f['family'] for f in r.json()['items']]

    for family in families:
        if family not in families_on_gf:
            raise Exception('Family {} does not exist on Google Fonts!'.format(family))


def github_dir(url):
    """Download fonts from a github repo directory"""
    fonts = []
    branch, api_url = _convert_github_url_to_api(url)
    request = requests.get(api_url, params={'ref': branch})
    api_request = json.loads(request.text)
    for item in api_request:
        dl_url = item['download_url']
        file_path = os.path.join(FONTS_DIR, item['name'])
        fonts.append(file_path)
        download_file(dl_url, file_path)
    return fonts


def user_upload(request, ajax_key):
    """Upload fonts from a user's system"""
    fonts = []
    for upload in request.files.getlist(ajax_key):
        filename = upload.filename
        destination = os.path.join(FONTS_DIR, filename)
        upload.save(destination)
        fonts.append(destination) 
    return fonts


def _convert_github_url_to_api(url):
    """Convert github html url to api url"""
    url = url.split('/')  # urls are always forward slash regardless of OS
    user, repo, branch, dirpath = url[3], url[4], url[6], url[7:]
    dirpath = '/'.join(dirpath)
    return branch, 'https://api.github.com/repos/%s/%s/contents/%s' %(
        user,
        repo,
        dirpath
    )


def _gf_download_url(families):
    """Assemble download url for families"""
    gf_url_prefix = 'https://fonts.google.com/download?family='
    families_name = [f.replace(' ', '%20') for f in families]
    families_url_suffix = '|'.join(families_name)
    return gf_url_prefix + families_url_suffix


def fonts_from_zip(zipfile, to):
    """download the fonts and store them locally"""
    unnest = False
    fonts = []
    for filename in zipfile.namelist():
        if filename.endswith(".ttf"):
            fonts.append(os.path.join(to, filename))
            zipfile.extract(filename, to)
        if '/' in filename:
            unnest = True
    if unnest:
        fonts = _unnest_folder(to)
    return fonts


def _unnest_folder(folder):
    """If multiple fonts have been downloaded, move them from sub dirs to
    parent dir"""
    fonts = []
    for r, path, files, in os.walk(folder):
        for file in files:
            if file.endswith('.ttf'):
                os.path.join(r, file)
                shutil.move(font_path, folder)
                new_font_path = os.path.join(folder, file)
                font.append(new_font_path)

    for f in os.listdir(folder):
        if os.path.isdir(os.path.join(folder, f)):
            os.rmdir(os.path.join(folder, f))
    return fonts

