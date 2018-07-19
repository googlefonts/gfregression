import os
import re
import shutil
import requests
from StringIO import StringIO
from blacklist import FONT_EXCEPTIONS
import json


# Info taken from https://caniuse.com/#feat=variable-fonts
MIN_VF_BROWSERS = {
    'chrome': 67,
    'firefox': 62,
    'edge': 17,
    'safari': 11,
}


def browser_supports_vfs(user_agent):
    """Check if the user's browser supports variable fonts

    Parameters
    ----------
    user_agent: werkzeug.useragents.UserAgent

    Returns
    -------
    Boolean"""
    user_browser = user_agent.browser
    browser_version = int(user_agent.version.split('.')[0])
    if browser_version < MIN_VF_BROWSERS[user_browser]:
        return False
    return True


def download_file(url, dst_path=None):
    """Download a file from a url. If no url is specified, store the file
    as a StringIO object"""
    request = requests.get(url, stream=True)
    if not dst_path:
        return StringIO(request.content)
    with open(dst_path, 'wb') as downloaded_file:
        shutil.copyfileobj(request.raw, downloaded_file)


def filename_to_family_name(path):
    '''Convert a fontpath into a font name.
    /path/to/SomeSans-Regular.ttf --> Some Sans'''
    filename = os.path.basename(path)[:-4]
    family = filename.split('-')[0]
    family = _convert_camelcase(family)
    return family


def _convert_camelcase(fam_name, seperator=' '):
    '''RubikMonoOne > Rubik Mono One'''
    if fam_name not in FONT_EXCEPTIONS:
        return re.sub('(?!^)([A-Z]|[0-9]+)', r'%s\1' % seperator, fam_name)
    else:
        fam_name = FONT_EXCEPTIONS[fam_name].replace(' ', seperator)
        return fam_name


with open("secrets.json") as f:
    secrets = json.loads(f.read())

def secret(key, secret=secrets):
    try:
        return secret[key]
    except KeyError:
        raise Exception('Secret {} does not exist'.format(secret))
