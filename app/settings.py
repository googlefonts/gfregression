import os

GLYPH_AREA_THRESHOLD = 7000
FONTS_DIR = os.path.join('static', 'fonts')
MEDIA_DIR = os.path.join('static', 'media')

DIFF_FAMILIES = True
if DIFF_FAMILIES:
    VIEWS = [
        'glyphs_all', 'glyphs_new', 'glyphs_missing', 'glyphs_modified',
        'marks_new', 'marks_missing', 'marks_modified',
        'mkmks_new', 'mkmks_missing', 'mkmks_modified',
        'kerns_new', 'kerns_missing', 'kerns_modified',
        'metrics_modified',
    ]
else:
    VIEWS = []
DIFF_LIMIT = 800
