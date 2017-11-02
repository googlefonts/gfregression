"""
Module for retrieving fonts
"""
import json
import requests
import os
import re
from zipfile import ZipFile
from StringIO import StringIO

from utils import download_file
from blacklist import FONT_EXCEPTIONS


def github_dir(url, to_dir):
    """Download fonts from a github repo directory"""
    branch, api_url = _convert_github_url_to_api(url)
    request = requests.get(api_url, params={'ref': branch})
    api_request = json.loads(request.text)
    for item in api_request:
        dl_url = item['download_url']
        file_path = os.path.join(to_dir, item['name'])
        download_file(dl_url, file_path)


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


def google_fonts(to_dir, *families):
    """Download a collection of font families from Google Fonts"""
    url = _gf_download_url(*families)
    fonts_zip = ZipFile(download_file(url))
    fonts_from_zip(fonts_zip, to_dir)


def _gf_download_url(families):
    """Assemble download url for families"""
    gf_url_prefix = 'https://fonts.google.com/download?family='
    families_name = set([_convert_camelcase(f.split('-')[0], '%20')
                        for f in families if f.endswith('.ttf')])
    families_url_suffix = '|'.join(families_name)
    return gf_url_prefix + families_url_suffix


def _convert_camelcase(fam_name, seperator=' '):
    '''RubikMonoOne > Rubik+Mono+One'''
    if fam_name not in FONT_EXCEPTIONS:
        return re.sub('(?!^)([A-Z]|[0-9]+)', r'%s\1' % seperator, fam_name)
    else:
        fam_name = FONT_EXCEPTIONS[fam_name].replace(' ', seperator)
        return fam_name


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


def user_upload(request, ajax_key, fonts_path):
    """Upload fonts from a users system"""
    for upload in request.files.getlist(ajax_key):
        filename = upload.filename.rsplit("/")[0]
        destination = "/".join([fonts_path, filename])
        upload.save(destination)
