"""Module to assemble families from ttfs and diff families"""
import os
import re
import uuid
from copy import deepcopy
from diffenator.font import DFont
from diffenator.diff import DiffFonts
from diffenator.dump import dump_glyphs
from gfregression import downloadfonts
import json

current_dir = os.path.dirname(__file__)

with open(os.path.join(current_dir, "gf_families_ignore_camelcase.json")) as f:
    GF_FAMILY_IGNORE_CAMEL = json.loads(f.read())


GF_WEIGHTS = [
    'Thin',
    'ExtraLight',
    'Light',
    'Regular',
    'Medium',
    'SemiBold',
    'Bold',
    'ExtraBold',
    'Black',
]
GF_WIDTHS = [
    "UltraCondensed",
    "ExtraCondensed",
    "Condensed",
    "SemiCondensed",
    "",
    "SemiExpanded",
    "Expanded",
    "ExtraExpanded",
    "UltraExpanded",
]

def find_closest_substring(string, items):
    for item in sorted(items, key=lambda k: len(k), reverse=True):
        if item.lower() in string.lower():
            return item
    return ""


def familyname_from_filename(filename, seperator=' '):
    """RubikMonoOne-Regular > Rubik Mono One"""
    family = filename.split('-')[0]
    if family not in list(GF_FAMILY_IGNORE_CAMEL.keys()):
        return re.sub('(?!^)([A-Z]|[0-9]+)', r'%s\1' % seperator, family)
    return GF_FAMILY_IGNORE_CAMEL[family]


def stylename_from_filename(filename):
    if filename.endswith(".ttf"):
        filename = filename[:-4]
    width = find_closest_substring(filename, GF_WIDTHS)
    if "-" in filename:
        stylename = filename.split("-")[1]
    else:
        stylename = "Regular"
    return width + stylename


class Font:
    """
    Wrapper for a ttf font with GF specific attributes.

    Parameters
    ----------
    path: str
        path to ttf

    """
    USWEIGHT_CLASS_TO_CSS_WEIGHT = {
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

    USWIDTH_CLASS_TO_CSS_STRETCH = {
        50: "50%",
        62.5: "62.5%",
        75: "75%",
        87.5: "87.5%",
        100: "100%",
        112.5: "112.5%",
        125: "125%",
        150: "150%",
        200: "200%",
    }

    def __init__(self, path, family_name=None, style_name=None):
        self.path = path
        self.filename = os.path.basename(self.path)[:-4]
        self.font = DFont(self.path)
        self._is_vf = self.is_vf
        if not family_name:
            self.family_name = familyname_from_filename(self.filename)
        else:
            self.family_name = family_name
        self.styles = []
        if style_name and not self._is_vf:
            style = FontStyle(style_name, self)
            self.styles.append(style)
        elif not style_name and not self._is_vf:
            style_name = stylename_from_filename(self.filename)
            style = FontStyle(style_name, self)
            self.styles.append(style)
        elif self._is_vf:
            self._get_vf_styles()
        self.axes = self._get_axes()

    def set_family_name(self, name):
        self.family_name = name

    @property
    def is_vf(self):
        if 'fvar' in self.font.ttfont:
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
                font-style: %s;
            """ % (self.path, self.family_name,
                   'italic' if self.font.ttfont["post"].italicAngle != 0. else "normal")
            if 'wght' in self.axes:
                try:
                    min_wght = self.USWEIGHT_CLASS_TO_CSS_WEIGHT[self.axes['wght'].minValue]
                    max_wght = self.USWEIGHT_CLASS_TO_CSS_WEIGHT[self.axes['wght'].maxValue]
                except KeyError:
                    raise Exception("wght axis not in range 100-900")
                string += '\nfont-weight: {} {};'.format(
                    min_wght,
                    max_wght
                )
            if 'wdth' in self.axes:
                try:
                    min_wdth = self.USWIDTH_CLASS_TO_CSS_STRETCH[self.axes['wdth'].minValue]
                    max_wdth = self.USWIDTH_CLASS_TO_CSS_STRETCH[self.axes['wdth'].maxValue]
                except KeyError:
                    raise Exception("wdth axis not in range 75-100")
                string += '\nfont-stretch: {} {};'.format(
                    min_wdth,
                    max_wdth
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
                font-stretch: %s;
                font-style: %s;
                font-family: %s;}""" % (
                    self.path,
                    self.styles[0].css_weight,
                    self.styles[0].css_width_name,
                    self.styles[0].css_style,
                    self.family_name,
                )

    def _get_vf_styles(self):
        instance_names = [
            self.font.ttfont['name'].getName(i.subfamilyNameID, 3, 1, 1033).toUnicode()
            for i in self.font.ttfont['fvar'].instances
        ]
        for style_name in instance_names:
            style = FontStyle(style_name, self)
            self.styles.append(style)

    def _get_axes(self):
        axes = {}
        if 'fvar' in self.font.ttfont:
            for axis in self.font.ttfont['fvar'].axes:
                axes[axis.axisTag] = axis
        return axes


class FontStyle:

    CSS_WEIGHTS = {
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
    CSS_WIDTH_VALS = {
        'UltraCondensed': 50,
        'ExtraCondensed': 62.5,
        'Condensed': 75,
        'SemiCondensed': 87.5,
        '': 100,
        'SemiExpanded': 112.5,
        'Expanded': 125,
        'ExtraExpanded': 150,
        'UltraExpanded': 200,
    }
    CSS_WIDTH_NAMES = {
        'UltraCondensed': 'ultra-condensed',
        'ExtraCondensed': 'extra-condensed',
        'Condensed': 'condensed',
        'SemiCondensed': 'semi-condensed',
        '': 'normal',
        'SemiExpanded': 'semi-expanded',
        'Expanded': 'expanded',
        'ExtraExpanded': 'extra-expanded',
        'UltraExpanded': 'ultra-expanded',
    }
    WEIGHTS = GF_WEIGHTS
    WIDTHS = GF_WIDTHS

    def __init__(self, style, font):
        """Get GF spec style info from a filename or an fvar instance entry."""
        self.name = style.replace(" ", "")
        self.font = font

        self.weight = find_closest_substring(self.name, GF_WEIGHTS)
        self.width = find_closest_substring(self.name, GF_WIDTHS)
        self.italic = self._get_italic()

        self.css_name = self.name
        self.css_weight = self.CSS_WEIGHTS[self.weight]
        self.css_width_name = self.CSS_WIDTH_NAMES[self.width]
        self.css_width_val = self.CSS_WIDTH_VALS[self.width]
        self.css_style = 'normal' if not self.italic else 'italic'

    def _get_italic(self):
        if "Oblique" in self.name:
            return True
        return True if "Italic" in self.name else False

    @property
    def css_class(self):
        return """
            .%s{
                font-weight: %s;
                font-variation-settings: "wdth" %s;
                font-stretch: %s;
                font-style: %s;
            }
        """ % (
                self.css_name,
                self.css_weight,
                self.css_width_val,
                self.css_width_name,
                self.css_style
            )


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


def family_from_googlefonts(family_name, dst, api_key=None,
                            include_width_families=False):
    """Get a family from Google Fonts

    Parameters
    ----------
    family_name: str
        Name of family on Google Fonts, can use spaces e.g 'Roboto Condensed'

    Returns
    -------
    family: Family"""
    if not api_key:
        api_key = os.environ["GF_API_KEY"]

    googlefonts = downloadfonts.GoogleFonts(api_key)
    if include_width_families:
        family = Family()
        gf_families = googlefonts.width_families(family_name)
        for width_family in gf_families:
            fonts = googlefonts.download_family(width_family, dst)
            for path in fonts:
                filename = os.path.basename(path)[:-4]
                style_name = stylename_from_filename(filename)
                uuid_file = os.path.join(dst, str(uuid.uuid4()) + '.ttf')
                os.rename(path, uuid_file)
                family.append(uuid_file, family_name, style_name)
        return family

    fonts = googlefonts.download_family(family_name, dst)
    return _create_family(fonts, dst)


def family_from_github_dir(url, dst):
    """Get a family from a github dir e.g
    https://github.com/googlefonts/comfortaa/tree/master/fonts/TTF

    Parameters
    url: str
        github url for dir

    Returns
    -------
    family: Family
    """
    fonts = downloadfonts.github_dir(url, dst)
    return _create_family(fonts, dst)


def family_from_user_upload(request, dst):
    """Get a family from a user upload"""
    fonts = downloadfonts.user_upload(request, dst)
    return _create_family(fonts, dst)


def _create_family(paths, dst):
    """Create a Family from a list of paths"""
    family = Family()
    for path in paths:
        filename = os.path.basename(path)[:-4]
        family_name = familyname_from_filename(filename)
        style_name = stylename_from_filename(filename)
        uuid_file = os.path.join(dst, str(uuid.uuid4()) + '.ttf')
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
        font_a = styles_before[style].font.font
        font_b = styles_after[style].font.font

        if font_a.is_variable and not font_b.is_variable:
            font_a.set_variations_from_static(font_b)

        elif not font_a.is_variable and font_b.is_variable:
            font_b.set_variations_from_static(font_a)
        # TODO (M Foley) vfs against vfs

        style_diff = DiffFonts(
            font_a,
            font_b,
            settings=dict(
                to_diff=set(['glyphs', 'kerns', 'marks', 'names', 'mkmks', 'metrics'])
            ),
        )
        for cat in style_diff._data:
            for subcat in style_diff._data[cat]:
                diff = {
                    'uuid': uuid,
                    'title': '{} {}'.format(cat.title(), subcat.title()),
                    'view': '{}_{}'.format(cat, subcat),
                    'font_before': styles_before[style].full_name,
                    'font_after': styles_after[style].full_name,
                    'items': style_diff._data[cat][subcat]._data
                }
                diffs.append(diff)
    return list(map(_diff_serialiser, diffs))


def families_glyphs_all(family_before, family_after, uuid):
    """Dump every glyph for each font in family_before.

    This diff is useful to see whether family_after can access all the glyphs
    in family_before

    Parameters
    ----------
    input_font: InputFont

    Returns
    -------
    glyphs: list
    """
    styles_before = {s.name: s for f in family_before.fonts for s in f.styles}
    styles_after = {s.name: s for f in family_after.fonts for s in f.styles}

    shared_styles = set(styles_before) & set(styles_after)
    items = []
    for style in shared_styles:
        font_a = styles_before[style].font.font
        font_b = styles_after[style].font.font

        all_glyphs = {
            'uuid': uuid,
            'title': 'Glyph All',
            'view': 'glyphs_all',
            'font_before': styles_before[style].name,
            'font_after': styles_after[style].name,
            'items': dump_glyphs(styles_before[style].font.font)._data,
        }
        items.append(all_glyphs)
    return list(map(_diff_serialiser, items))


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
        if hasattr(d[k], 'key'):
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
        styles=[s.name for f in family_before.fonts for s in f.styles
                if s.name in shared_styles],
        has_vfs=any([family_before.has_vfs, family_after.has_vfs])
    )

