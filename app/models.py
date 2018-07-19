import os
from uuid import uuid4
from diffenator import diff_fonts
from diffenator.font import InputFont
from diffenator.glyphs import dump_glyphs
from settings import FONTS_DIR
from fontTools.ttLib import TTFont


CSS_WEIGHT = {
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


class NoMatchingFonts(Exception):
    def __init__(self, set1_name, set1, set2_name, set2):
        self.set1_name = set1_name
        self.set1 = set1
        self.set2_name = set2_name
        self.set2 = set2
        Exception.__init__(self, 'No matching fonts found between sets {}: [{}] & {}: [{}]'.format(
                self.set1_name,
                ', '.join(self.set1),
                self.set2_name,
                ', '.join(self.set2),
            ))


def _get_family_name_and_style(filename):
    """Get the family name and style name from a font's filename"""
    file_info = filename[:-4].split('-')
    if len(file_info) >= 2 and 'VF' not in file_info:
        family_name = file_info[0]
        style = file_info[1]
    elif len(file_info) == 2 and 'VF' in file_info:
        family_name = file_info[0]
        style = 'Regular'
    else:
        family_name = file_info[0]
        style = 'Regular'
    return family_name, style


def _get_vf_axises(ttfont):
    if 'fvar' in ttfont:
        return [{'name': a.axisTag, 'min': a.minValue, 'max': a.maxValue}
                for a in ttfont['fvar'].axes]
    return None


def _get_vf_styles(ttfont):
    """Get the vf instances from the fvar table"""
    styles = []
    for style in ttfont['fvar'].instances:
        nameid = style.subfamilyNameID
        style = ttfont['name'].getName(nameid, 3, 1, 1033).toUnicode()
        styles.append(style.replace(' ', ''))
    if not styles:
        raise exception('No instances included in fvar table.')
    return styles


def add_fonts(fonts_paths, position, uuid):
    fonts = []
    for path in fonts_paths:
        fonts.append(add_font(path, position, uuid))
    return fonts


def add_font(path, position, uuid):
    if not path.endswith('ttf'):
        raise Exception('{} is not a ttf'.format(path))
    filename = os.path.basename(path)
    ttfont = TTFont(path)
    family_name, style = _get_family_name_and_style(filename)
    font_type = 'variable' if 'fvar' in ttfont else 'static'
    axises = _get_vf_axises(ttfont)
    styles = [style] if font_type == 'static' else _get_vf_styles(ttfont)
    # Rename font so we don't get colliding filenames
    unique_filename = str(uuid4()) + '.ttf'
    unique_path = os.path.join(FONTS_DIR, unique_filename)
    os.rename(path, unique_path)

    return {
        "uuid": uuid,
        "filename": unique_path,
        "family_name": family_name,
        "type": font_type,
        "axises": axises,
        "styles": styles,
        "position": position,
        "id": '{}-{}'.format(family_name, position)
    }


def _get_font_styles(fonts):
    styles = {}
    for font in fonts:
        for style in font['styles']:
            key = '{}-{}'.format(font['family_name'], style)
            if key not in styles:
                styles[key] = font
    return styles


def match_styles(styles_before, styles_after):
    """Match fonts_before and fonts_after by styles."""
    styles_before_h = {f['match']: f for f in styles_before}
    styles_after_h = {f['match']: f for f in styles_after}
    matching = set(styles_before_h) & set(styles_after_h)
    if not matching:
        raise NoMatchingFonts('Fonts Before',
                      [f['full_name'] for f in styles_before],
                      'Fonts After',
                      [f['full_name'] for f in styles_after],
        )
    styles_before = [styles_before_h[style] for style in sorted(matching)]
    styles_after = [styles_after_h[style] for style in sorted(matching)]
    return styles_before, styles_after


def add_fontset(fonts_before, styles_before, fonts_after, styles_after, uuid):
    """Gen css for added fonts"""
    return {
        'uuid': uuid,
        'css_classes': map(_gen_css_class, styles_before),
        'before': {
            'family_name': fonts_before[0]['family_name'],
            'css_family_name': fonts_before[0]['id'],
            'css_fontfaces': set(map(_gen_css_font_face, fonts_before)),
        },
        'after': {
            'family_name': fonts_after[0]['family_name'],
            'css_family_name': fonts_after[0]['id'],
            'css_fontfaces': set(map(_gen_css_font_face, fonts_after)),
        },
    }


def add_styles(fonts):
    styles = []
    for font in fonts:
        if font['type'] == 'static':
            weight = _get_css_weight_from_style(font['styles'][0])
            style = {
                'filename': font['filename'],
                'weight': weight,
                'style': 'italic' if 'Italic' in font['styles'][0] else 'normal',
                'full_name': '{}-{}-{}'.format(
                    font['family_name'],
                    weight,
                    'italic' if 'Italic' in font['styles'][0] else 'normal',
                ),
                'match': '{}-{}'.format(font['family_name'], font['styles'][0]),
                'position': font['position'],
                'family_name': font['family_name'],
            }
            styles.append(style)

        if font['type'] == 'variable':
            for style in font['styles']:
                weight = _get_css_weight_from_style(style)
                style = {
                    'filename': font['filename'],
                    'weight': weight,
                    'style': 'italic' if 'Italic' in style else 'normal',
                    'full_name': '{}-{}'.format(
                        font['family_name'],
                        weight,
                        'italic' if 'Italic' in font['styles'][0] else 'normal',
                        font['position'],
                    ),
                    'match': '{}-{}'.format(font['family_name'], style),
                    'position': font['position'],
                    'family_name': font['family_name'],
                }
                styles.append(style)
    return styles


def _gen_css_font_face(font):
    if font['type'] == 'static':
        css_weight = _get_css_weight_from_style(font['styles'][0])
        css_style = 'italic' if 'Italic' in font['styles'][0] else 'normal'
        css = ('@font-face {font-family: %s; '
               'src: url(/%s); font-weight: %s; '
               'font-style: %s;') % (
                   font['id'],
                   font['filename'],
                   css_weight,
                   css_style
                )

    elif font['type'] == 'variable':
        css = ('@font-face {font-family: %s; '
               'src: url(/%s); ') % (
                   font['id'],
                   font['filename'],
                )
        for axis in font['axises']:
            if axis['name'] == 'wght':
                css += 'font-weight: {} {}; '.format(
                    axis['min'], axis['max']
                )
            if axis['name'] == 'slnt':
                css += 'font-style: oblique {}deg {}deg; '.format(
                    axis['min'], axis['max']
                )
            if axis['name'] == 'wdth':
                css += 'font-stretch: {}%% {}%%; '.format(
                    axis['min'], axis['max']
                )
    css += '}'
    return css


def _gen_css_class(style):
    return '.%s {font-weight: %s; font-style: %s;}' % (
        style['full_name'],
        style['weight'],
        style['style'],
    )


def _get_css_weight_from_style(font_style):
    style_window = sorted(CSS_WEIGHT.keys(), key=lambda k: len(k),
                          reverse=True)
    for style in style_window:
        if style in font_style:
            return CSS_WEIGHT[style]
    return 400


def add_font_diffs(fonts_before, fonts_after, uuid):
    diffs = []
    for font_before, font_after in zip(fonts_before, fonts_after):
        input_font_before = InputFont(font_before['filename'])
        input_font_after = InputFont(font_after['filename'])

        font_diff = diff_fonts(
            input_font_before,
            input_font_after,
        )

        for cat in font_diff:
            # TODO (M Foley) users should be able to diff what cats they want
            # in diffenator.
            if cat not in ['glyphs', 'kerns', 'marks', 'mkmks', 'metrics']:
                continue
            for subcat in font_diff[cat]:
                diff = {
                    'uuid': uuid,
                    'title': '{} {}'.format(cat.title(), subcat.title()),
                    'view': '{}_{}'.format(cat, subcat),
                    'font_before': font_before['full_name'],
                    'font_after': font_after['full_name'],
                    'items': font_diff[cat][subcat]
                }
                diffs.append(diff)

        all_glyphs = {
            'uuid': uuid,
            'title': 'Glyph All',
            'view': 'glyphs_all',
            'font_before': font_before['full_name'],
            'font_after': font_after['full_name'],
            'items': dump_glyphs(input_font_before),
        }
        diffs.append(all_glyphs)
    return map(_comparisons_serialiser, diffs)


def _comparisons_serialiser(d):
    """Serialise diffenator's diff object"""
    for k in d:
        if isinstance(d[k], dict):
            _comparisons_serialiser(d[k])
        elif isinstance(d[k], list):
            for idx, item in enumerate(d[k]):
                _comparisons_serialiser(item)
        elif hasattr(d[k], 'kkey'):
            d[k] = dict(d[k].__dict__)
    return d
