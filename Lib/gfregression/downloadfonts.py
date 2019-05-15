"""
Module for downloading fonts
"""
import json
import requests
import os
import re
from zipfile import ZipFile
import shutil
import uuid

try:
    from StringIO import StringIO
except ModuleNotFoundError:  # py3 workaround
    from io import BytesIO as StringIO


def download_file(url, dst=None):
    """Download a file from a url. If no url is specified, store the file
    as a StringIO object"""
    request = requests.get(url, stream=True)
    if not dst:
        return StringIO(request.content)
    with open(dst, 'wb') as downloaded_file:
        shutil.copyfileobj(request.raw, downloaded_file)


class GoogleFonts(object):
    """Primitive python client to control Googlefonts api and fonts.google.com"""
    def __init__(self, api_key=None):
        if not api_key:
            self.api_key = os.environ["GF_API_KEY"]
        else:
            self.api_key = api_key
        self.data = self._get_api_data()
        self.families = [f['family'] for f in self.data['items']]

    def _get_api_data(self):
        api_url = 'https://www.googleapis.com/webfonts/v1/webfonts?key={}'.format(
            self.api_key
        )
        return requests.get(api_url).json()

    def download_family(self, family, dst):
        """Download a collection of font families from Google Fonts"""
        has_family = self.has_family(family)
        if not has_family:
            raise Exception('Family {} does not exist on Google Fonts!'.format(family))
        url = 'https://fonts.google.com/download?family={}'.format(
            family.replace(' ', '%20')
        )
        fonts_zip = ZipFile(download_file(url))
        fonts_paths = _fonts_from_zip(fonts_zip, dst)
        return fonts_paths

    def has_family(self, family):
        """Check if Google Fonts has the specified font family"""
        if family in self.families:
            return True
        return False

    def related_families(self, string):
        results = []
        for family in self.families:
            if string in family:
                results.append(family)
        return results

    def width_families(self, string):
        results = []
        for family in self.families:
            if (string in family and "Condensed" in family) or \
               (string in family and "Expanded" in family):
                   results.append(family)
        if results:
            results.insert(0, string)
        return results


def github_dir(url, dst):
    """Download fonts from a github repo directory"""
    fonts = []
    branch, api_url = _convert_github_url_to_api(url)
    request = requests.get(api_url, params={'ref': branch})
    api_request = json.loads(request.text)
    for item in api_request:
        if not 'download_url' in item:
            raise Exception('Directory contains no fonts')
        dl_url = item['download_url']
        file_path = os.path.join(dst, item['name'])
        fonts.append(file_path)
        download_file(dl_url, file_path)
    return fonts


def user_upload(files, dst):
    """Upload fonts from a user's system"""
    fonts = []
    for f in files:
        destination = os.path.join(dst, f.filename)
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


def _fonts_from_zip(zipfile, dst):
    """download the fonts and store them locally"""
    fonts = []
    for filename in zipfile.namelist():
        if filename.endswith(".ttf"):
            target = os.path.join(dst, filename)
            zipfile.extract(filename, dst)
            fonts.append(target)
    return fonts

