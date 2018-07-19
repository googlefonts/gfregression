from fontTools.ttLib import TTFont, newTable
from family import (
    Family,
    Font,
    FontStyle,
    from_googlefonts,
    from_github_dir
)
import tempfile
import os
import unittest


class TestFamily(unittest.TestCase):
    def setUp(self):
        self.path_1 = tempfile.mktemp() + '.ttf'
        self.font_1 = TTFont()
        self.font_1['name'] = newTable('name')
        self.font_1['name'].setName(u'Roboto', 1, 3, 1, 1033)
        self.font_1.save(self.path_1)

        self.path_2 = tempfile.mktemp() + '.ttf'
        self.font_2 = TTFont()
        self.font_2['name'] = newTable('name')
        self.font_2['name'].setName(u'Roboto', 1, 3, 1, 1033)
        self.font_2.save(self.path_2)

        self.path_3 = tempfile.mktemp() + '.ttf'
        self.font_3 = TTFont()
        self.font_3['name'] = newTable('name')
        self.font_3['name'].setName(u'Roboto Condensed', 1, 3, 1, 1033)
        self.font_3.save(self.path_3)

    def tearDown(self):
        os.remove(self.path_1)
        os.remove(self.path_2)
        os.remove(self.path_3)

    def test_append(self):
        family = Family()
        family.append(self.path_1)
        family.append(self.path_2)
        self.assertEqual(family.name, u'Roboto')

    # def test_append_font_which_does_not_belong_to_family(self):
    #     family = Family()
    #     family.append(self.path_1)
    #     family.append(self.path_2)
    #     self.failureException(family.append(self.path_3))


class TestFont(unittest.TestCase):

    def test_get_family_name(self):
        """Test case taken from Roboto Black, https://www.github.com/google/roboto

        For fonts which are non RIBBI, the family name field (id 1) often includes
        the style name. The font will also have the preferred family name (id 16)
        included. For RIBBI fonts, nameid 1 is fine, for non RIBBI we want nameid 16
        """
        self.path = tempfile.mktemp() + '.ttf'
        self.ttfont = TTFont()
        self.ttfont['name'] = newTable('name')
        self.ttfont['name'].setName(u'Roboto Black', 1, 3, 1, 1033)
        self.ttfont['name'].setName(u'Roboto', 16, 3, 1, 1033)
        self.ttfont.save(self.path)

        self.font = Font(self.path)
        self.assertEqual(self.font.family_name, u'Roboto')
        os.remove(self.path)

    def test_static_get_styles(self):
        self.path = tempfile.mktemp() + '.ttf'
        self.ttfont = TTFont()
        self.ttfont['name'] = newTable('name')
        self.ttfont['name'].setName(u'Roboto', 1, 3, 1, 1033)
        self.ttfont['name'].setName(u'Regular', 2, 3, 1, 1033)
        self.ttfont['name'].setName(u'Black', 17, 3, 1, 1033)
        self.ttfont.save(self.path)   

        self.font = Font(self.path)
        self.assertEqual(self.font.styles[0].name, 'Black')
        os.remove(self.path) 

    def test_vf_get_styles(self):
        pass


class TestFontStyle(unittest.TestCase):
    def setUp(self):
        font = TTFont()
        font['name'] = newTable('name')
        font['name'].setName(u'Roboto', 1, 3, 1, 1033)
        self.font_path = tempfile.mktemp()
        font.save(self.font_path)
        self.font = Font(self.font_path)

    def tearDown(self):
        os.remove(self.font_path)

    def test_weight_class(self):
        style = FontStyle('Italic', self.font)
        self.assertEqual(400, style.weight_class)

        style = FontStyle('Black Italic', self.font)
        self.assertEqual(900, style.weight_class)

        style = FontStyle('Condensed Medium', self.font)
        self.assertEqual(500, style.weight_class)

        style = FontStyle('Expanded Thin', self.font)
        self.assertEqual(100, style.weight_class)

    def test_is_italic(self):
        style = FontStyle('Italic', self.font)
        self.assertEqual(True, style.italic)

        style = FontStyle('Bold Italic', self.font)
        self.assertEqual(True, style.italic)

        style = FontStyle('BoldItalic', self.font)
        self.assertEqual(True, style.italic)


class TestFromFamily(unittest.TestCase):
    """TODO (M Foley) these tests should not use network requests.
    They should be replced with mock objects"""
    def test_family_from_googlefonts(self):
        family = from_googlefonts('Roboto')
        self.assertEqual('Roboto', family.name)

    def test_family_from_github_dir(self):
        family = from_github_dir('https://github.com/googlefonts/comfortaa/tree/master/fonts/TTF')
        self.assertEqual('Comfortaa', family.name)

    def test_family_from_user_upload(self):
        pass


class TestDiffFamilies(unittest.TestCase):

    def test_diff_families(self):
        pass


if __name__ == '__main__':
    unittest.main()
