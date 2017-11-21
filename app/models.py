import os
from uuid import uuid4
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

def add_fonts(fonts_paths, font_type, uuid):
    fonts = []
    for path in fonts_paths:
        fonts.append(add_font(path, font_type, uuid))
    return fonts


def add_font(path, font_type, uuid):
    """Rename font to uuid and derive css properties from filename"""
    filename = os.path.basename(path)
    family_name, style = filename[:-4].split('-')
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
    return {
        'uuid': uuid,
        'before': {
            'family_name': fonts_before[0]['family_name'],
            'css_family_name': fonts_before[0]['css_family_name'],
            'ttfs': [f for f in fonts_before if f['full_name'] in shared_fonts],
        },
        'after': {
            'family_name': fonts_after[0]['family_name'],
            'css_family_name': fonts_after[0]['css_family_name'],
            'ttfs': [f for f in fonts_after if f['full_name'] in shared_fonts],
        },
    }