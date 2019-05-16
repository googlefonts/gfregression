import os
import re
import shutil
import requests
import json
try:
    from StringIO import StringIO
except ModuleNotFoundError:  # py3 workaround
    from io import BytesIO as StringIO


current_dir = os.path.dirname(__file__)

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
    if user_browser not in MIN_VF_BROWSERS:
        return False
    if browser_version < MIN_VF_BROWSERS[user_browser]:
        return False
    return True



with open(os.path.join(current_dir, "secrets.json")) as f:
    secrets = json.loads(f.read())

def secret(key, secret=secrets):
    try:
        return secret[key]
    except KeyError:
        raise Exception('Secret {} does not exist'.format(secret))
