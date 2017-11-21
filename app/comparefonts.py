#TODO (M Foley) use fontdiffenator when its ready

from fontTools.ttLib import TTFont
from fontTools.pens.areaPen import AreaPen
from fontTools.misc.py23 import unichr
from settings import GLYPH_AREA_THRESHOLD


def glyphs_new(font_before, font_after):
    """Return glyphs which are new"""
    return _subtract_glyphs(font_after, font_before)


def glyphs_missing(font_before, font_after):
    """Return glyphs which are missing"""
    return _subtract_glyphs(font_before, font_after)


def _subtract_glyphs(font_before, font_after):
    """Subtract font_before's glyphs against font_after's glyphs"""
    glyphs_before = font_before['glyf'].keys()
    glyphs_after = font_after['glyf'].keys()
    glyphs_leftover = set(glyphs_before) - set(glyphs_after)

    # TODO fontdiffenator will be able to get unencoded glyphs
    before_cmap_tbl = font_before['cmap'].getcmap(3, 1).cmap
    after_cmap_tbl = font_after['cmap'].getcmap(3, 1).cmap

    after_encoded_glyphs = [i[0] for i in after_cmap_tbl.items()]
    return [g for g in before_cmap_tbl.items() if g[1] in glyphs_leftover
            and g[0] not in after_encoded_glyphs]


def glyphs_modified(font_before, font_after):
    """For glyphs which are shared between the two fonts, return glyphs
    who's surface areas differ and the diff is greater than a
    predetermined threshold"""
    bad_glyphs = []
    glyphs_before = font_before.getGlyphSet()
    glyphs_after = font_after.getGlyphSet()
    glyphs_shared = set(glyphs_before.keys()) & set(glyphs_after.keys())

    upm_before = font_before['head'].unitsPerEm
    upm_after = font_after['head'].unitsPerEm

    pen_before = AreaPen(glyphs_before)
    pen_after = AreaPen(glyphs_after)

    for glyph in glyphs_shared:
        glyphs_before[glyph].draw(pen_before)
        glyphs_after[glyph].draw(pen_after)

        area_before = pen_before.value
        pen_before.value = 0
        area_after = pen_after.value
        pen_after.value = 0

        area_norm_before = (area_before / upm_before) * upm_after
        area_norm_after = (area_after / upm_after) * upm_before

        if area_norm_before != area_norm_after:
            if abs(area_norm_before - area_norm_after) > GLYPH_AREA_THRESHOLD:
                bad_glyphs.append(glyph)
    
    glyphs_encoded = font_before['cmap'].getcmap(3,1).cmap
    return [i for i in glyphs_encoded.items() if i[1] in bad_glyphs]


def compare_fonts(fonts_before, fonts_after, uuid):
    comparisons = {'uuid': uuid,
                   'glyphs_missing': {
                        'title': 'Glyphs Missing',
                        'tests': []},
                   'glyphs_new': {
                        'title': 'Glyphs New',
                        'tests': []},
                    'glyphs_modified': {
                        'title': 'Glyphs modified',
                        'tests': []},
                   }
    shared_fonts = set([f['full_name'] for f in fonts_before]) & \
                   set([f['full_name'] for f in fonts_after])
    fonts_before = {f['full_name']: f for f in fonts_before}
    fonts_after = {f['full_name']: f for f in fonts_after}

    for font in shared_fonts:
        font_before_path = fonts_before[font]['filename']
        font_after_path = fonts_after[font]['filename']
        font_before = TTFont(font_before_path)
        font_after = TTFont(font_after_path)

        g_missing = glyphs_missing(font_before, font_after)
        comparisons['glyphs_missing']['tests'].append({
                'font_before': fonts_before[font],
                'font_after': fonts_after[font],
                'glyphs': _dict_cmap_glyphs(g_missing)
        })
        g_new = glyphs_new(font_before, font_after)
        comparisons['glyphs_new']['tests'].append({
            'font_before': fonts_before[font],
            'font_after': fonts_after[font],
            'glyphs': _dict_cmap_glyphs(g_new)
        })
        g_modified = glyphs_modified(font_before, font_after)
        comparisons['glyphs_modified']['tests'].append({
            'font_before': fonts_before[font],
            'font_after': fonts_after[font],
            'glyphs': _dict_cmap_glyphs(g_modified),
        })
    return comparisons


def _dict_cmap_glyphs(cmap_glyphs):
    """[(ordinal, name)...] --> [{'char': uniXXXX, 'name': name}]"""
    mp = []
    for uni, name in cmap_glyphs:
        mp.append({'char': unichr(uni), 'name': name})
    return mp