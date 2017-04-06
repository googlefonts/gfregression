from fontTools.pens.areaPen import AreaPen
from otlang2iso import otlang2iso
from script2iso import script2iso
from models import db, Languages


def _local_vs_remote_fonts(func, local_fonts, remote_fonts):
    """Return family glyphs which differ against remote family"""
    fonts = {}

    for font in local_fonts:
        fonts[font] = func(
            local_fonts[font].font,
            remote_fonts[font].font,
        )
    return fonts


def modified_family_glyphs(local_fonts, remote_fonts):
    """return glyphs which have changed from local to remote"""
    return _local_vs_remote_fonts(modified_glyphs, local_fonts, remote_fonts)


def missing_family_glyphs(local_fonts, remote_fonts):
    """Return glyphs which are missing in local fonts when compared 
    against the remote fonts"""
    return _local_vs_remote_fonts(missing_glyphs, local_fonts, remote_fonts)


def new_family_glyphs(local_fonts, remote_fonts):
    """Return glyphs which are new in local fonts"""
    return _local_vs_remote_fonts(new_glyphs, local_fonts, remote_fonts)


def modified_glyphs(local_font, remote_font):
    modified_glyphs = []
    l_glyphs = local_font.getGlyphNames()
    r_glyphs = remote_font.getGlyphNames()
    shared_glyphs = set(l_glyphs) & set(r_glyphs)

    l_glyf = local_font.getGlyphSet()
    r_glyf = remote_font.getGlyphSet()

    l_pen = AreaPen(l_glyf)
    r_pen = AreaPen(r_glyf)

    for glyph in shared_glyphs:
        l_glyf[glyph].draw(l_pen)
        r_glyf[glyph].draw(r_pen)

        l_area = l_pen.value
        l_pen.value = 0
        r_area = r_pen.value
        r_pen.value = 0

        if l_area != r_area:
            if int(l_area) ^ int(r_area) > 0:
                modified_glyphs.append(glyph)

    l_cmap_tbl = local_font['cmap'].getcmap(3, 1).cmap
    try:
        return [g for g in l_cmap_tbl.items() if g[1] in modified_glyphs]
    except:
        print('%s has consistent glyphs' % local_font)
    return modified_glyphs


def new_glyphs(local_font, remote_font):
    local_glyphs = local_font.getGlyphNames()
    remote_glyphs = remote_font.getGlyphNames()
    new_glyphs = set(local_glyphs) - set(remote_glyphs)

    l_cmap_tbl = local_font['cmap'].getcmap(3, 1).cmap
    return [g for g in l_cmap_tbl.items() if g[1] in new_glyphs]


def missing_glyphs(local_font, remote_font):
    """Find if local_font is missing any glyphs against remote_font"""
    local_glyphs = local_font.getGlyphNames()
    remote_glyphs = remote_font.getGlyphNames()
    missing_glyphs = set(remote_glyphs) - set(local_glyphs)

    r_cmap_tbl = remote_font['cmap'].getcmap(3, 1).cmap
    return [g for g in r_cmap_tbl.items() if g[1] in missing_glyphs]


def gsub_languages(fonts):
    """for each defined gsub language, download and return some
    sample text"""
    font_languages = {}
    for font in fonts:
        script_records = fonts[font].font['GSUB'].table.ScriptList.ScriptRecord

        font_languages[font] = {}
        for script in script_records:
            font_languages[font][script2iso[script.ScriptTag]] = ''
            languages = list(script.Script.LangSysRecord)
            for language in languages:
                lang_tag = language.LangSysTag
                font_languages[font][lang_tag] = ''

        for lang_tag in font_languages[font]:
            try:
                db.connect()
                db_language = Languages.get(Languages.part3 == otlang2iso[lang_tag])
                font_languages[font][lang_tag] = db_language
                db.close()
            except:
                all # Need to add other OpenType scripts to script2iso
    return font_languages
