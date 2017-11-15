from fontTools.pens.areaPen import AreaPen
from otlang2iso import otlang2iso
from script2iso import script2iso
from models import db, Languages
from settings import GLYPH_THRESHOLD


class CompareFonts:

    def __init__(self, fonts_before, fonts_after):
        self.fonts_before = {f.fullname: f for f in fonts_before}
        self.fonts_after = {f.fullname: f for f in fonts_after}
        self.shared_fonts = set(self.fonts_before) & set(self.fonts_after)

    def inconsistent_glyphs(self):
        """return glyphs which have changed from local to remote"""
        glyphs = {}
        bad_glyphs = {}

        for font in self.shared_fonts:
            l_glyphs = self.fonts_after[font].font['glyf'].glyphs.keys()
            r_glyphs = self.fonts_before[font].font['glyf'].glyphs.keys()
            shared_glyphs = set(l_glyphs) & set(r_glyphs)

            l_upm = self.fonts_after[font].font['head'].unitsPerEm 
            r_upm = self.fonts_before[font].font['head'].unitsPerEm

            l_glyphs = self.fonts_after[font].font.getGlyphSet()
            r_glyphs = self.fonts_before[font].font.getGlyphSet()

            l_pen = AreaPen(l_glyphs)
            r_pen = AreaPen(r_glyphs)

            for glyph in shared_glyphs:
                l_glyphs[glyph].draw(l_pen)
                r_glyphs[glyph].draw(r_pen)

                l_area = l_pen.value
                l_pen.value = 0
                r_area = r_pen.value
                r_pen.value = 0

                l_area_norm = (l_area / l_upm) * r_upm
                r_area_norm = (r_area / r_upm) * l_upm

                if l_area_norm != r_area_norm:
                    if abs(l_area_norm - r_area_norm) > GLYPH_THRESHOLD:

                        if font not in bad_glyphs:
                            bad_glyphs[font] = []
                        bad_glyphs[font].append(glyph)

            l_cmap_tbl = self.fonts_after[font].font['cmap'].getcmap(3, 1).cmap
            try:
                glyphs[font] = [i for i in l_cmap_tbl.items() if i[1] in bad_glyphs[font]]
            except:
                print('%s has consistent glyphs' % font)
        return glyphs

    def new_glyphs(self):
        """Return glyphs which are new in local fonts"""
        glyphs = {}

        for font in self.shared_fonts:
            l_glyphs = self.fonts_after[font].font['glyf'].glyphs.keys()
            r_glyphs = self.fonts_before[font].font['glyf'].glyphs.keys()
            glyphs[font] = set(l_glyphs) - set(r_glyphs)

            l_cmap_tbl = self.fonts_after[font].font['cmap'].getcmap(3, 1).cmap

            r_cmap_tbl = self.fonts_before[font].font['cmap'].getcmap(3, 1).cmap
            r_encoded_glyphs = [i[0] for i in r_cmap_tbl.items()]

            glyphs[font] = [i for i in l_cmap_tbl.items() if i[1] in glyphs[font] and
                            i[0] not in r_encoded_glyphs]
        return glyphs

    def missing_glyphs(self):
        """Return glyphs which are missing in local fonts"""
        glyphs = {}

        for font in self.shared_fonts:
            l_glyphs = self.fonts_after[font].font['glyf'].glyphs.keys()
            r_glyphs = self.fonts_before[font].font['glyf'].glyphs.keys()
            glyphs[font] = set(r_glyphs) - set(l_glyphs)

            l_cmap_tbl = self.fonts_after[font].font['cmap'].getcmap(3, 1).cmap
            l_encoded_glyphs = [i[0] for i in l_cmap_tbl.items()]
            r_cmap_tbl = self.fonts_before[font].font['cmap'].getcmap(3, 1).cmap

            glyphs[font] = [i for i in r_cmap_tbl.items() if i[1] in glyphs[font] and
                            i[0] not in l_encoded_glyphs]
        return glyphs

    def languages(self):
        """for each defined gsub language, download and return some
        sample text"""
        font_languages = {}
        for font in self.fonts_after:
            try:
                script_records = self.fonts_after[font].font['GSUB'].table.ScriptList.ScriptRecord

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
            except KeyError:
                print('Skipping language tests, no GSUB table')
                return None
        return font_languages
