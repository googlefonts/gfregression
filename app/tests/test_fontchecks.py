import unittest
import os
import sys
import shutil
import tempfile
import difflib
from fontTools.ttLib import TTFont
from app.fontchecks import (
    missing_glyphs,
    new_glyphs,
    modified_glyphs,
)


class GlyphTableComparisons(unittest.TestCase):

    def setUp(self):
        self.tempdir = None
        self.num_tempfiles = 0

    def tearDown(self):
        if self.tempdir:
            shutil.rmtree(self.tempdir)

    @staticmethod
    def getpath(testfile):
        path, _ = os.path.split(__file__)
        return os.path.join(path, "data", testfile)

    def temp_path(self, suffix):
        if not self.tempdir:
            self.tempdir = tempfile.mkdtemp()
        self.num_tempfiles += 1
        return os.path.join(self.tempdir,
                            "tmp%d%s" % (self.num_tempfiles, suffix))

    def read_ttx(self, path):
        lines = []
        with open(path, "r", encoding="utf-8") as ttx:
            for line in ttx.readlines():
                # Elide ttFont attributes because ttLibVersion may change,
                # and use os-native line separators so we can run difflib.
                if line.startswith("<ttFont "):
                    lines.append("<ttFont>" + os.linesep)
                else:
                    lines.append(line.rstrip() + os.linesep)
        return lines

    def expect_ttx(self, font, expected_ttx, tables):
        path = self.temp_path(suffix=".ttx")
        font.saveXML(path, tables=tables)
        actual = self.read_ttx(path)
        expected = self.read_ttx(expected_ttx)
        if actual != expected:
            for line in difflib.unified_diff(
                    expected, actual, fromfile=expected_ttx, tofile=path):
                sys.stdout.write(line)
            self.fail("TTX output is different from expected")

    def compile_font(self, path, suffix):
        savepath = self.temp_path(suffix=suffix)
        font = TTFont(recalcBBoxes=False, recalcTimestamp=False)
        font.importXML(path)
        font.save(savepath, reorderTables=None)
        return font, savepath

# -----
# TESTS


    def test_modified_glyphs(self):
        _, font_full = self.compile_font(self.getpath("testfamily.ttx"), ".ttf")
        _, font_modified_a = self.compile_font(self.getpath("testfamily-modified-A.ttx"), ".ttf")
        font_full = TTFont(font_full)
        font_modified_a = TTFont(font_modified_a)
        modified_a = modified_glyphs(font_modified_a, font_full)
        self.assertEqual(modified_a, [(65, 'A')])

    def test_missing_glyphs(self):
        _, font_full = self.compile_font(self.getpath("testfamily.ttx"), ".ttf")
        _, font_missing_c = self.compile_font(self.getpath("testfamily-missing-C.ttx"), ".ttf")
        font_full = TTFont(font_full)
        font_missing_c = TTFont(font_missing_c)
        missing_c = missing_glyphs(font_missing_c, font_full)
        self.assertEqual(missing_c, [(67, 'C')])

    def test_new_glyphs(self):
        _, font_full = self.compile_font(self.getpath("testfamily.ttx"), ".ttf")
        _, font_new_d = self.compile_font(self.getpath("testfamily-new-D.ttx"), ".ttf")
        font_full = TTFont(font_full)
        font_new_d = TTFont(font_new_d)
        new_d = new_glyphs(font_new_d, font_full)
        self.assertEqual(new_d, [(68, 'D')])


if __name__ == '__main__':
    unittest.main()
