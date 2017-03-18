from fontTools.pens.areaPen import AreaPen
from otlang2iso import otlang2iso
from script2iso import script2iso
from models import db, Languages

GLYPH_THRESHOLD = 0

def inconsistent_fonts_glyphs(local_fonts, remote_fonts):
    """return glyphs which have changed from local to remote"""
    glyphs = {}
    bad_glyphs = {}

    for font in local_fonts:
        l_glyphs = local_fonts[font].font['glyf'].glyphs.keys()
        r_glyphs = remote_fonts[font].font['glyf'].glyphs.keys()
        shared_glyphs = set(l_glyphs) & set(r_glyphs)

        l_glyphs = local_fonts[font].font.getGlyphSet()
        r_glyphs = remote_fonts[font].font.getGlyphSet()

        l_pen = AreaPen(l_glyphs)
        r_pen = AreaPen(r_glyphs)

        for glyph in shared_glyphs:
            l_glyphs[glyph].draw(l_pen)
            r_glyphs[glyph].draw(r_pen)

            l_area = l_pen.value
            l_pen.value = 0
            r_area = r_pen.value
            r_pen.value = 0

            if l_area != r_area:
                if int(l_area) ^ int(r_area) > GLYPH_THRESHOLD:

                    if font not in bad_glyphs:
                        bad_glyphs[font] = []
                    bad_glyphs[font].append(glyph)

        l_cmap_tbl = local_fonts[font].font['cmap'].getcmap(3, 1).cmap
        try:
            glyphs[font] = [i for i in l_cmap_tbl.items() if i[1] in bad_glyphs[font]]
        except:
            print('%s has consistent glyphs' % font)
    return glyphs

def new_fonts_glyphs(local_fonts, remote_fonts):
    """Return glyphs which are new in local fonts"""
    glyphs = {}

    for font in local_fonts:
        l_glyphs = local_fonts[font].font['glyf'].glyphs.keys()
        r_glyphs = remote_fonts[font].font['glyf'].glyphs.keys()
        glyphs[font] = set(l_glyphs) - set(r_glyphs)

        l_cmap_tbl = local_fonts[font].font['cmap'].getcmap(3, 1).cmap

        r_cmap_tbl = remote_fonts[font].font['cmap'].getcmap(3, 1).cmap
        r_encoded_glyphs = [i[0] for i in r_cmap_tbl.items()]

        glyphs[font] = [i for i in l_cmap_tbl.items() if i[1] in glyphs[font] and
                        i[0] not in r_encoded_glyphs]
    return glyphs

def missing_fonts_glyphs(local_fonts, remote_fonts):
    """Return glyphs which are missing in local fonts"""
    glyphs = {}

    for font in local_fonts:
        l_glyphs = local_fonts[font].font['glyf'].glyphs.keys()
        r_glyphs = remote_fonts[font].font['glyf'].glyphs.keys()
        glyphs[font] = set(r_glyphs) - set(l_glyphs)

        l_cmap_tbl = local_fonts[font].font['cmap'].getcmap(3, 1).cmap
        l_encoded_glyphs = [i[0] for i in l_cmap_tbl.items()]
        r_cmap_tbl = remote_fonts[font].font['cmap'].getcmap(3, 1).cmap

        glyphs[font] = [i for i in r_cmap_tbl.items() if i[1] in glyphs[font] and
                        i[0] not in l_encoded_glyphs]
    return glyphs

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
