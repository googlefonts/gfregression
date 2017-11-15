"""
Font Manager
~~~~~~~~

Module to deal with the creation and deletion of font folders in
static dir's fonts_after and fonts_before sub dirs.
"""
from datetime import datetime
import os
import shutil
from glob import glob
import ntpath
from fontTools.ttLib import TTFont
import uuid

from models import gfr_font

ROOT = os.path.dirname(__file__)
FONTS_BEFORE_ROOT = os.path.join(ROOT, 'static', 'fonts_before')
FONTS_AFTER_ROOT = os.path.join(ROOT, 'static', 'fonts_after')
LIMIT = 10


def directories():
    return [f for f in os.listdir(FONTS_BEFORE_ROOT) if
            os.path.isdir(os.path.join(FONTS_BEFORE_ROOT, f))]


def new():
    current_directories = directories()
    date = datetime.now()
    _id = len(current_directories) + 1
    uid = str(uuid.uuid4())
    manager = FontManager(uid)
    manager.mkdirs()
    return manager


def load(uid):
    return FontManager(uid)


def has_fonts(uid):
    directory = os.path.join(FONTS_AFTER_ROOT, uid)
    return os.path.isdir(directory)


class FontManager(object):

    def __init__(self, uid):
        self.uid = uid
        self.before_dir = os.path.join(FONTS_BEFORE_ROOT, uid)
        self.after_dir = os.path.join(FONTS_AFTER_ROOT, uid)

        self.fonts_before = self._get_fonts(self.before_dir, 'fonts_before')
        self.fonts_after = self._get_fonts(self.after_dir, 'fonts_after')

    def mkdirs(self):
        """Create the base and target dirs"""
        os.mkdir(self.before_dir)
        os.mkdir(self.after_dir)

    def equalize_fonts(self):
        """Delete any fonts which are not in both directories"""
        shared_fonts = list(set(os.listdir(self.before_dir)) & \
                            set(os.listdir(self.after_dir)))        
        self._keep_fonts(self.after_dir, shared_fonts)
        self._keep_fonts(self.before_dir, shared_fonts)
        self.refresh()

    def _keep_fonts(self, font_dir, fonts):
        for font in os.listdir(font_dir):
            if font not in fonts:
                font_path = os.path.join(font_dir, font)
                os.remove(font_path)

    def refresh(self):
        """Reload session font changes"""
        self.fonts_before = self._get_fonts(self.before_dir, 'fonts_before')
        self.fonts_after = self._get_fonts(self.after_dir, 'fonts_after')

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


def remove_font_dirs():
    """Remove all font dirs"""
    map(_delete_dirs, (FONTS_BEFORE_ROOT, FONTS_AFTER_ROOT))


def _delete_dirs(path):
    """Delete previous sessions"""
    for item in os.listdir(path):
        if os.path.isdir(os.path.join(path, item)):
            shutil.rmtree(os.path.join(path, item))
