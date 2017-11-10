"""
Font Manager
~~~~~~~~

Module to deal with the creation and deletion of font folders in
static dir's targetfonts and basefonts sub dirs.
"""
from datetime import datetime
import os
import shutil
from glob import glob
import ntpath
from fontTools.ttLib import TTFont
from models import gfr_font


BASE_FONTS_ROOT = os.path.join('static', 'basefonts')
TARGET_FONTS_ROOT = os.path.join('static', 'targetfonts')
LIMIT = 10


def directories():
    return [f for f in os.listdir(BASE_FONTS_ROOT) if
            os.path.isdir(os.path.join(BASE_FONTS_ROOT, f))]


def new():
    current_directories = directories()
    if len(current_directories) >= LIMIT:
        _remove_sessions()
        current_directories = []

    date = datetime.now()
    _id = len(current_directories) + 1
    uid = '{}-{}-{}-{}'.format(date.year, date.month, date.day, _id)
    manager = FontManager(uid)
    manager.mkdirs()
    return manager


def load(uid):
    return FontManager(uid)


def has_fonts(uid):
    directory = os.path.join(TARGET_FONTS_ROOT, uid)
    return os.path.isdir(directory)


class FontManager(object):

    def __init__(self, uid):
        self.uid = uid
        self.base_dir = os.path.join(BASE_FONTS_ROOT, uid)
        self.target_dir = os.path.join(TARGET_FONTS_ROOT, uid)

        self.base_fonts = self._get_fonts(self.base_dir, 'base_fonts')
        self.target_fonts = self._get_fonts(self.target_dir, 'target_fonts')

    def mkdirs(self):
        """Create the base and target dirs"""
        os.mkdir(self.base_dir)
        os.mkdir(self.target_dir)

    def equalize_fonts(self):
        """Delete any fonts which are not in both directories"""
        shared_fonts = list(set(os.listdir(self.base_dir)) & \
                            set(os.listdir(self.target_dir)))        
        self._keep_fonts(self.target_dir, shared_fonts)
        self._keep_fonts(self.base_dir, shared_fonts)
        self.refresh()

    def _keep_fonts(self, font_dir, fonts):
        for font in os.listdir(font_dir):
            if font not in fonts:
                font_path = os.path.join(font_dir, font)
                os.remove(font_path)

    def refresh(self):
        """Reload session font changes"""
        self.base_fonts = self._get_fonts(self.base_dir, 'base_fonts')
        self.target_fonts = self._get_fonts(self.target_dir, 'target_fonts')

    def _get_fonts(self, path, suffix):
        fonts = []
        fonts_paths = glob(path + '/*.ttf')
        if not fonts_paths:
            return None
        for path in fonts_paths:
            name = ntpath.basename(path)[:-4]
            font = gfr_font(
                path=path.replace('\\', '/'),
                fullname=name,
                cssname='%s-%s' % (name, suffix),
            )
            fonts.append(font)
        return fonts


def _remove_sessions():
    """Remove all sessions"""
    map(_delete_dirs, (BASE_FONTS_ROOT, TARGET_FONTS_ROOT))


def _delete_dirs(path):
    """Delete previous sessions"""
    for item in os.listdir(path):
        if os.path.isdir(os.path.join(path, item)):
            shutil.rmtree(os.path.join(path, item))
