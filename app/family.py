"""Module to assemble families from ttfs and diff families"""
import os
import re
import uuid
from copy import deepcopy
from diffenator.font import InputFont
from diffenator.diff import diff_fonts
from diffenator.utils import vf_instance_from_static
from diffenator.glyphs import dump_glyphs
import downloadfonts
from settings import FONTS_DIR
from utils import family_name_from_filename, style_name_from_filename


class Font:
    """
    Wrapper for a ttf font with GF specific attributes.

    Parameters
    ----------
    path: str
        path to ttf

    """
    OS2_TO_CSS_WEIGHT = {
        100: 100,
        200: 200,
        250: 100, # static gf Thin
        275: 200, # static gf ExtraLight
        300: 300,
        400: 400,
        500: 500,
        600: 600,
        700: 700,
        800: 800,
        900: 900
    }

    def __init__(self, path, family_name=None, style_name=None):
        self.path = path
        self.filename = os.path.basename(self.path)[:-4]
        self.font = InputFont(self.path)
        self._is_vf = self.is_vf
        if not family_name:
            self.family_name = family_name_from_filename(self.filename)
        else:
            self.family_name = family_name
        self.styles = []
        if style_name and not self._is_vf:
            style = FontStyle(style_name, self)
            self.styles.append(style)
        elif not style_name and not self._is_vf:
            style_name = style_name_from_filename(self.filename)
            style = FontStyle(style_name, self)
            self.styles.append(style)
        elif self._is_vf:
            self._get_vf_styles()
        self.axes = self._get_axes()

    def set_family_name(self, name):
        self.family_name = name

    @property
    def is_vf(self):
        if 'fvar' in self.font:
            return True
        return False

    @property
    def css_font_face(self):
        """Generate a @font_face for the font.

        If the font is a variable font, include axis ranges.

        Returns
        -------
        string: str
            string for css @font_Face
        """
        if self._is_vf:
            string = """@font-face{
                src: url(/%s);
                font-family: %s;
            """ % (self.path, self.family_name)
            if 'wght' in self.axes:
                try:
                    min_wght = self.OS2_TO_CSS_WEIGHT[self.axes['wght'].minValue]
                    max_wght = self.OS2_TO_CSS_WEIGHT[self.axes['wght'].maxValue]
                except KeyError:
                    raise Exception("wght axis not in range 100-900")
                string += '\nfont-weight: {} {};'.format(
                    min_wght,
                    max_wght
                )
            if 'slnt' in self.axes:
                string += '\nfont-style: oblique {}deg {}deg;'.format(
                    self.axes['slnt'].minValue,
                    self.axes['slnt'].maxValue
                )
            string += '}'
            return string
        else:
            return """@font-face{
                src: url(/%s);
                font-weight: %s;
                font-style: %s;
                font-family: %s;}""" % (
                    self.path,
                    self.styles[0].weight_class,
                    'italic' if self.styles[0].italic else 'normal',
                    self.family_name,
                )

    def _get_vf_styles(self):
        instance_names = [
            self.font['name'].getName(i.subfamilyNameID, 3, 1, 1033).toUnicode()
            for i in self.font['fvar'].instances
        ]
        for style_name in instance_names:
            style = FontStyle(style_name, self)
            self.styles.append(style)

    def _get_axes(self):
        axes = {}
        if 'fvar' in self.font:
            for axis in self.font['fvar'].axes:
                axes[axis.axisTag] = axis
        return axes


class FontStyle:
    """Style which exists within a Font. If Font is static, then there's only
    one style. If Font is a variable font, there may be multiple styles.

    Parameters
    ----------
    name: str
        The name for the style
    font: Font
        The font which holds the style
    """

    WEIGHT_MAP = {
        'Thin': 100,
        'ExtraLight': 200,
        'Light': 300,
        'Regular': 400,
        '': 400,
        'Medium': 500,
        'SemiBold': 600,
        'Bold': 700,
        'ExtraBold': 800,
        'Black': 900,
    }

    def __init__(self, name, font):
        self.name = name.replace(' ', '-')
        self.font = font
        self.full_name = '{}-{}'.format(
            self.font.family_name.replace(' ', '-'), self.name
        )
        self.weight_class = self._get_weight_class()
        self.width_class = self._get_width_class()
        self.italic = True if 'Italic' in self.name else False

    def _get_weight_class(self):
        """Extract the weight from the style name"""
        for weight in sorted(self.WEIGHT_MAP.keys(), key=lambda k: len(k), reverse=True):
            if weight.lower() in self.name.lower():
                return self.WEIGHT_MAP[weight]
        raise Exception("{} is not supported. Only supports {}".format(
            self.name, self.WEIGHT_MAP.keys())
        )

    def _get_width_class(self):
        # TODO (M Foley)
        return None

    @property
    def css_class(self):
        font_style = 'normal' if not self.italic else 'italic'
        string = """.%s{
            font-weight: %s;
            font-style: %s;
        }
        """ % (self.full_name.replace(' ', '-'), self.weight_class, font_style)
        return string


class Family:
    """Container for Fonts which belong a family"""
    def __init__(self):
        self.name = None
        self.fonts = []
        self._has_vfs = self.has_vfs

    def append(self, font_path, family_name=None, style_name=None):
        """append font"""
        if not family_name and not style_name:
            font = Font(font_path)
        else:
            font = Font(font_path, family_name, style_name)
        if not self.name:
            self.name = font.family_name
        if font.family_name != self.name:
            raise Exception(
                ('"%s" does not belong to the famiy "%s". Fonts '
                 'must belong to the same family.' % (
                    font.family_name, self.name))
                )
        self.fonts.append(font)

    def set_name(self, name):
        """Update the family's name. This will also change each font's name and also
        any references to the family name in any styles"""
        self.name = name
        for font in self.fonts:
            font.set_family_name(name)

    @property
    def has_vfs(self):
        """Determine whether the family has variable fonts"""
        return any([f.is_vf for f in self.fonts])


def from_googlefonts(family_name):
    """Get a family from Google Fonts and save the files to GFR's static dir

    Parameters
    ----------
    family_name: str
        Name of family on Google Fonts, can use spaces e.g 'Roboto Condensed'

    Returns
    -------
    family: Family"""
    fonts = downloadfonts.googlefonts(family_name)
    return create_family(fonts)


def from_github_dir(url):
    """Get a family from a github dir e.g
    https://github.com/googlefonts/comfortaa/tree/master/fonts/TTF

    Parameters
    url: str
        github url for dir

    Returns
    -------
    family: Family
    """
    fonts = downloadfonts.github_dir(url)
    return create_family(fonts)


def from_user_upload(request):
    """Get a family from a user upload"""
    fonts = downloadfonts.user_upload(request)
    return create_family(fonts)


def create_family(paths):
    """Create a Family from a list of paths"""
    family = Family()
    for path in paths:
        filename = os.path.basename(path)[:-4]
        family_name = family_name_from_filename(filename)
        style_name = style_name_from_filename(filename)
        uuid_file = os.path.join(FONTS_DIR, str(uuid.uuid4()) + '.ttf')
        os.rename(path, uuid_file)
        family.append(uuid_file, family_name, style_name)
    return family

def diff_families(family_before, family_after, uuid):
    """Diff two families which have the same family name.

    Uses fontdiffenator.

    Parameters
    ---------
    family_before: Family
    family_after: Family

    Returns
    -------
    reports: list
    """
    styles_before = {s.name: s for f in family_before.fonts for s in f.styles}
    styles_after = {s.name: s for f in family_after.fonts for s in f.styles}

    shared_styles = set(styles_before) & set(styles_after)
    diffs = []
    for style in shared_styles:
        font_a = deepcopy(styles_before[style].font.font)
        font_b = deepcopy(styles_after[style].font.font)

        if 'fvar' in font_a and 'fvar' not in font_b:
            font_a = vf_instance_from_static(font_a, font_b)

        elif 'fvar' not in font_a and 'fvar' in font_b:
            font_b = vf_instance_from_static(font_b, font_a)

        style_diff = diff_fonts(
            font_a,
            font_b,
            categories_to_diff=['glyphs', 'kerns', 'marks', 'names', 'mkmks', 'metrics'],
        )
        for cat in style_diff:
            for subcat in style_diff[cat]:
                diff = {
                    'uuid': uuid,
                    'title': '{} {}'.format(cat.title(), subcat.title()),
                    'view': '{}_{}'.format(cat, subcat),
                    'font_before': styles_before[style].full_name,
                    'font_after': styles_after[style].full_name,
                    'items': style_diff[cat][subcat]
                }
                diffs.append(diff)
        # even though this isn't a diff it's convientient to add it.
        all_glyphs = {
            'uuid': uuid,
            'title': 'Glyph All',
            'view': 'glyphs_all',
            'font_before': styles_before[style].full_name,
            'font_after': styles_after[style].full_name,
            'items': dump_glyphs(styles_before[style].font.font),
        }
        diffs.append(all_glyphs)
    return map(_diff_serialiser, diffs)


def _diff_serialiser(d):
    """Serialise diffenator's diff object"""
    for k in d:
        if isinstance(d[k], dict):
            _diff_serialiser(d[k])
        if isinstance(d[k], list):
            for idx, item in enumerate(d[k]):
                _diff_serialiser(item)
        if hasattr(d[k], 'font'):
            d[k].font = None
        if hasattr(d[k], 'kkey'):
            d[k] = dict(d[k].__dict__)
    return d


def get_families(family_before, family_after, uuid):
    family_before.set_name(family_before.name + '-before')
    family_after.set_name(family_after.name + '-after')

    styles_before = {s.name: s for f in family_before.fonts for s in f.styles}
    styles_after = {s.name: s for f in family_after.fonts for s in f.styles}

    shared_styles = set(styles_before) & set(styles_after)
    return dict(
        uuid=uuid,
        before=dict(
            name=family_before.name,
            css_font_faces=[f.css_font_face for f in family_before.fonts],
        ),
        after=dict(
            name=family_after.name,
            css_font_faces=[f.css_font_face for f in family_after.fonts],
        ),
        css_classes=[s.css_class for f in family_before.fonts for s in f.styles
                     if s.name in shared_styles],
        styles=[s.full_name for f in family_before.fonts for s in f.styles
                if s.name in shared_styles],
        has_vfs=any([family_before.has_vfs, family_after.has_vfs])
    )
