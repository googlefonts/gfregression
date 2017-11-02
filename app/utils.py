import shutil
import requests
from StringIO import StringIO


def download_file(url, dst_path=None):
    """Download a file from a url. If no url is specified, store the file
    as a StringIO object"""
    request = requests.get(url, stream=True)
    if not dst_path:
        return StringIO(request.content)
    with open(dst_path, 'wb') as downloaded_file:
        shutil.copyfileobj(request.raw, downloaded_file)
