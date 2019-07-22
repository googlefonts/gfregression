from gfregression import (
    Family,
    Font,
    FontStyle,
    family_from_googlefonts,
    family_from_github_dir,
    familyname_from_filename,
    get_families,
    diff_families,
    families_glyphs_all,

)
import tempfile
import os
import shutil
import unittest
from glob import glob


class TestFamily(unittest.TestCase):

    def setUp(self):
        current_dir = os.path.dirname(__file__)
        roboto_fonts_dir = os.path.join(current_dir, "data", "Roboto")
        self.roboto_fonts = glob(os.path.join(roboto_fonts_dir, "*.ttf"))

    def test_append(self):
        family = Family()
        for path in self.roboto_fonts:
            family.append(path)
            family.append(path)
        self.assertEqual(family.name, 'Roboto')

    # def test_append_font_which_does_not_belong_to_family(self):
    #     family = Family()
    #     family.append(self.path_1)
    #     family.append(self.path_2)
    #     self.failureException(family.append(self.path_3))


class TestFont(unittest.TestCase):
 
    def setUp(self):
        cwd = os.path.dirname(__file__)
        font_path = os.path.join(cwd, 'data', 'Roboto', 'Roboto-BoldItalic.ttf')
        self.font = Font(font_path)

        vf_font_path = os.path.join(cwd, 'data', 'Cabin', 'Cabin-VF.ttf')
        self.vf_font = Font(vf_font_path)

    def test_get_family_name(self):
        """Test case taken from Roboto Black, https://www.github.com/google/roboto

        For fonts which are non RIBBI, the family name field (id 1) often includes
        the style name. The font will also have the preferred family name (id 16)
        included. For RIBBI fonts, nameid 1 is fine, for non RIBBI we want nameid 16
        """
        self.assertEqual(self.font.family_name, u'Roboto')

    def test_static_get_style(self):
        self.assertEqual(self.font.styles[0].name, 'BoldItalic')

    def test_vf_get_styles(self):
        styles = [s.name for s in self.vf_font.styles]
        self.assertIn("CondensedRegular", styles)
        self.assertIn("Regular", styles)

 
 
class TestFontStyle(unittest.TestCase):
    def setUp(self):
        cwd = os.path.dirname(__file__)
        font_path = os.path.join(cwd, 'data', 'Roboto')
        font_file = os.path.join(font_path, "Roboto-Regular.ttf")
        self.font = Font(font_file)

    def test_weight_class(self):
        style = FontStyle('Italic', self.font)
        self.assertEqual(400, style.css_weight)

        style = FontStyle('Black Italic', self.font)
        self.assertEqual(900, style.css_weight)

        style = FontStyle('Condensed Medium', self.font)
        self.assertEqual(500, style.css_weight)

        style = FontStyle('Expanded Thin', self.font)
        self.assertEqual(100, style.css_weight)

    def test_width_class(self):
        style = FontStyle("SemiExpanded Black Italic", self.font)
        self.assertEqual(112.5, style.css_width_val)

        style = FontStyle("Semi Expanded Black Italic", self.font)
        self.assertEqual(112.5, style.css_width_val)

        style = FontStyle("Ultra Condensed Thin", self.font)
        self.assertEqual(50, style.css_width_val)

        style = FontStyle("UltraCondensed Thin Italic", self.font)
        self.assertEqual(50, style.css_width_val)

    def test_is_italic(self):
        style = FontStyle('Italic', self.font)
        self.assertEqual(True, style.italic)

        style = FontStyle('Bold Italic', self.font)
        self.assertEqual(True, style.italic)

        style = FontStyle('BoldItalic', self.font)
        self.assertEqual(True, style.italic)

 
class TestFromFamily(unittest.TestCase):
    """TODO (M Foley) these tests should not use network requests.
    They should be replaced with mock objects"""
    def test_family_from_googlefonts(self):
        with tempfile.TemporaryDirectory() as fp:
            family = family_from_googlefonts('Amatic SC', fp)
            self.assertEqual('Amatic SC', family.name)

    def test_family_from_googlefonts_with_width_families(self):
        with tempfile.TemporaryDirectory() as fp:
            family = family_from_googlefonts("Cabin", fp, include_width_families=True)
            styles = [f.styles[0].name for f in family.fonts]
            self.assertIn("CondensedBold", styles)

    def test_family_from_github_dir(self):
        with tempfile.TemporaryDirectory() as fp:
            family = family_from_github_dir('https://github.com/googlefonts/comfortaa/tree/master/fonts/TTF', fp)
            self.assertEqual('Comfortaa', family.name)


class TestGetFamilies(unittest.TestCase):

    def setUp(self):
        current_dir = os.path.dirname(__file__)
        roboto_fonts_dir = os.path.join(current_dir, "data", "Roboto")
        self.roboto_fonts = glob(os.path.join(roboto_fonts_dir, "*.ttf"))

    def test_matching_styles(self):
        family_before = Family()
        for path in self.roboto_fonts:
            family_before.append(path)

        family_after = Family()
        for path in self.roboto_fonts:
            if "Italic" in path:
                continue
            family_after.append(path)

        uuid = "1234"
        family_match = get_families(family_before, family_after, uuid)
        self.assertEqual(sorted(["Regular", "Bold"]), sorted(family_match["styles"]))

    def test_familyname_from_filename(self):
        filename = "Kreon[wght].ttf"
        self.assertEqual("Kreon", familyname_from_filename(filename))

        filename = "Kreon-Regular.ttf"
        self.assertEqual("Kreon", familyname_from_filename(filename))

        filename = "Kreon-Italic-VF.ttf"
        self.assertEqual("Kreon", familyname_from_filename(filename))


    def test_matching_styles_with_widths_from_googlefonts(self):
        with tempfile.TemporaryDirectory() as fp_before, tempfile.TemporaryDirectory() as fp_after:
            family_before = family_from_googlefonts("Cabin", fp_before, include_width_families=True)
            family_after = family_from_googlefonts("Cabin Condensed", fp_after)
            uuid = "1234"
            family_match = get_families(family_before, family_after, uuid)
            styles = ["CondensedRegular", "CondensedMedium", "CondensedSemiBold", "CondensedBold"]
            self.assertEqual(sorted(styles), sorted(family_match["styles"]), uuid)


class TestDiffFamilies(unittest.TestCase):

    def setUp(self):
        current_dir = os.path.dirname(__file__)
        roboto_fonts_dir = os.path.join(current_dir, "data", "Roboto")
        self.roboto_fonts = glob(os.path.join(roboto_fonts_dir, "*.ttf"))
        self.family_before = Family()
        self.family_after = Family()
        for path in self.roboto_fonts:
            self.family_before.append(path)
            self.family_after.append(path)

    def test_diff_families(self):
        uuid = '1234'
        diff = diff_families(self.family_before, self.family_after, uuid)
        self.assertNotEqual(0, len(diff))

    def test_families_glyphs_all(self):
        uuid = '1234'
        diff = families_glyphs_all(self.family_before, self.family_after, uuid)
        self.assertNotEqual(0, len(diff))


class TestGoogleFontsAPI(unittest.TestCase):

    def setUp(self):
        from gfregression.downloadfonts import GoogleFonts
        self.googlefonts = GoogleFonts()

    def test_download_family(self):
        with tempfile.TemporaryDirectory() as fp:
            fonts = self.googlefonts.download_family("Comfortaa", fp)
            self.assertGreaterEqual(1, len(fonts))

    def test_sibling_families(self):
        families = self.googlefonts.related_families("Cabin")
        self.assertIn("Cabin Sketch", families)

    def test_width_families(self):
        families = self.googlefonts.width_families("Cabin")
        self.assertIn("Cabin Condensed", families)

    def test_has_family(self):
        family = self.googlefonts.has_family("Some Generic Family")
        self.assertEqual(False, family)

        family = self.googlefonts.has_family("Roboto")
        self.assertEqual(True, family)


if __name__ == '__main__':
    unittest.main()

