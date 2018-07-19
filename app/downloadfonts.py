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
import uuid

from utils import download_file, secret
from blacklist import FONT_EXCEPTIONS
from settings import FONTS_DIR


def googlefonts(family):
    """Download a collection of font families from Google Fonts"""
    has_family = _gf_has_family(family)
    if not has_family:
        raise Exception('Family {} does not exist on Google Fonts!'.format(family))
    url = 'https://fonts.google.com/download?family={}'.format(
        family.replace(' ', '%20')
    )
    fonts_zip = ZipFile(download_file(url))
    fonts_paths = _fonts_from_zip(fonts_zip, FONTS_DIR)
    return fonts_paths


def _gf_has_family(family):
    """Check if Google Fonts has the specified font family"""
    api_url = 'https://www.googleapis.com/webfonts/v1/webfonts?key={}'.format(
        secret('GF_API_KEY')
    )
    r = requests.get(api_url)
    families_on_gf = [f['family'] for f in r.json()['items']]
    if family in families_on_gf:
        return True
    return False


def github_dir(url):
    """Download fonts from a github repo directory"""
    fonts = []
    branch, api_url = _convert_github_url_to_api(url)
    request = requests.get(api_url, params={'ref': branch})
    api_request = json.loads(request.text)
    for item in api_request:
        if not 'download_url' in item:
            raise Exception('Directory contains no fonts')
        dl_url = item['download_url']
        file_path = os.path.join(FONTS_DIR, item['name'])
        fonts.append(file_path)
        download_file(dl_url, file_path)
    return fonts


def user_upload(files):
    """Upload fonts from a user's system"""
    fonts = []
    for f in files:
        filename = str(uuid.uuid4()) + '.ttf'
        destination = os.path.join(FONTS_DIR, filename)
        f.save(destination)
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


def _fonts_from_zip(zipfile, to):
    """download the fonts and store them locally"""
    fonts = []
    for filename in zipfile.namelist():
        if filename.endswith(".ttf"):
            current = os.path.join(to, filename)
            target = os.path.join(to, str(uuid.uuid4()) + '.ttf')
            zipfile.extract(filename, to)
            os.rename(current, target)
            fonts.append(target)
    return fonts
