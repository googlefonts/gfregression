import os
from uuid import uuid4
from diffenator import diff_fonts
from settings import FONTS_DIR


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

def add_fonts(fonts_paths, font_type, uuid):
    fonts = []
    for path in fonts_paths:
        fonts.append(add_font(path, font_type, uuid))
    return fonts


def add_font(path, font_type, uuid):
    """Rename font to uuid and derive css properties from filename"""
    filename = os.path.basename(path)
    if '-' in filename:
        family_name, style = filename[:-4].split('-')
    else:
        family_name = filename[:-4]
        style = 'Regular'
    css_family_name = '%s-%s' % (family_name, font_type)
    full_name = filename[:-4]
    weight = style.replace('Italic', '')

    # Rename font so we don't get colliding filenames
    unique_filename = str(uuid4()) + '.ttf'
    unique_path = os.path.join(FONTS_DIR, unique_filename)
    os.rename(path, unique_path)

    css_weight = CSS_WEIGHT[weight] if weight in CSS_WEIGHT else 400
    css_style = 'italic' if 'Italic' in style else 'normal'
    css_full_name = '%s-%s' % (full_name, font_type)
    font_face = ('@font-face {font-family: %s; '
                'src: url(/%s); font-weight: %s; '
                'font-style: %s;}') % (
                    css_family_name, unique_path, css_weight, css_style
                )
    span_class = '.%s {font-weight: %s; font-style: %s;}' % (
        css_full_name, css_weight, css_style
    )
    return {
        "uuid": uuid,
        "filename": unique_path,
        "family_name": family_name,
        "css_family_name": css_family_name,
        "style_name": style,
        "full_name": full_name,
        "position": font_type,
        "font_face": font_face,
        "span_class": span_class,
        "span_name": css_full_name,
    }


def add_fontset(fonts_before, fonts_after, uuid):
    shared_fonts = set([f['full_name'] for f in fonts_before]) & \
                   set([f['full_name'] for f in fonts_after])
    if len(shared_fonts) == 0:
        raise NoMatchingFonts('Fonts Before',
                              [f['full_name'] for f in fonts_before],
                              'Fonts After',
                              [f['full_name'] for f in fonts_after],
        )
    fonts_before = [f for f in fonts_before if f['full_name'] in shared_fonts]
    fonts_after = [f for f in fonts_after if f['full_name'] in shared_fonts]
    
    fonts_before_sorted = sorted(fonts_before, key=lambda n: n['full_name'])
    fonts_after_sorted = sorted(fonts_after, key=lambda n: n['full_name'])
    return {
        'uuid': uuid,
        'before': {
            'family_name': fonts_before[0]['family_name'],
            'css_family_name': fonts_before[0]['css_family_name'],
            'ttfs': fonts_before_sorted,
        },
        'after': {
            'family_name': fonts_after[0]['family_name'],
            'css_family_name': fonts_after[0]['css_family_name'],
            'ttfs': fonts_after_sorted,
        },
    }


def add_fonts_comparison(fonts_before, fonts_after, uuid):
    comparisons = {'uuid': uuid}
    shared_fonts = set([f['full_name'] for f in fonts_before]) & \
                   set([f['full_name'] for f in fonts_after])
    fonts_before = {f['full_name']: f for f in fonts_before}
    fonts_after = {f['full_name']: f for f in fonts_after}

    for font in shared_fonts:
        font_before_path = fonts_before[font]['filename']
        font_after_path = fonts_after[font]['filename']

        comparison = diff_fonts(font_before_path, font_after_path)

        for cat in comparison:
            if cat not in ('glyphs', 'kern', 'metrics', 'marks', 'mkmks'):
                continue
            for subcat in comparison[cat]:
                key = '{}_{}'.format(cat, subcat)
                if not key in comparisons:
                    title = '{} {}'.format(cat.title(), subcat.title())
                    comparisons[key] = {'title': title, 'tests': []}
                comparisons[key]['tests'].append({
                        'font_before': fonts_before[font],
                        'font_after': fonts_after[font],
                        'glyphs': comparison[cat][subcat]
                })
    _comparisons_serialiser(comparisons)
    return comparisons


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
