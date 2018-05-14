"""
Use Nototool's hbinput generator to get every accesible character
in a font.

TODO (M Foley) This approach is too slow on complex multilingual families
A better approach may be to assign puas to unencoded glyphs.
"""
from fontTools.ttLib import TTFont
from fontTools.misc.py23 import unichr
import nototools
from nototools.hb_input import HbInputGenerator


class HtmlInputGenerator(HbInputGenerator):
    """Output html escape sequences"""
    def all_inputs(self, warn=False):
        """Generate html inputs for all glyphs in a given font."""
        inputs = []
        glyph_set = self.font.getGlyphSet()
        for name in self.font.getGlyphOrder():
            is_zero_width = glyph_set[name].width == 0
            cur_input = self.input_from_name(name, pad=is_zero_width)
            if cur_input is not None:
                feat, char_seq = cur_input
                if feat == ('ccmp',):
                    char_seq = char_seq.replace(' ', '')
                inputs.append(
                    {'name': name, 'features': feat, 'characters': char_seq}
                )
            elif warn:
                print('not tested (unreachable?): %s' % name)
        return inputs

    def input_from_name(self, name, seen=None, pad=False):
        """Given glyph name, return input to harbuzz to render this glyph.

        Returns input in the form of a (features, text) tuple, where `features`
        is a list of feature tags to activate and `text` is an input string.

        Argument `seen` is used by the method to avoid following cycles when
        recursively looking for possible input. `pad` can be used to add
        whitespace to text output, for non-spacing glyphs.

        Can return None in two situations: if no possible input is found (no
        simple unicode mapping or substitution rule exists to generate the
        glyph), or if the requested glyph already exists in `seen` (in which
        case this path of generating input should not be followed further).
        """

        if name in self.memo:
            return self.memo[name]

        inputs = []

        # avoid following cyclic paths through features
        if seen is None:
            seen = set()
        if name in seen:
            return None
        seen.add(name)

        # see if this glyph has a simple unicode mapping
        if name in self.reverse_cmap:
            text = unichr(self.reverse_cmap[name])
            inputs.append(((), text))

        # check the substitution features
        inputs.extend(self._inputs_from_gsub(name, seen))
        # seen.remove(name)

        # since this method sometimes returns None to avoid cycles, the
        # recursive calls that it makes might have themselves returned None,
        # but we should avoid returning None here if there are other options
        inputs = [i for i in inputs if i is not None]
        if not inputs:
            return None

        features, text = min(inputs)
        # can't pad if we don't support space
        if pad and self.space_width > 0:
            width, space = self.widths[name], self.space_width
            padding = ' ' * (width // space + (1 if width % space else 0))
            text = padding + text
        self.memo[name] = features, text
        return self.memo[name]


def font_glyph_palette(font):
    combinations = HtmlInputGenerator(font)
    return combinations.all_inputs()


def fonts_all_glyphs(fonts_before, fonts_after, uuid):
    """..."""
    glyphs_all = {'uuid': uuid,
                  'glyphs_all': {
                      'title': 'Glyphs All',
                      'tests': []},
                  }
    shared_fonts = set([f['full_name'] for f in fonts_before]) & \
                   set([f['full_name'] for f in fonts_after])
    fonts_before = {f['full_name']: f for f in fonts_before}
    fonts_after = {f['full_name']: f for f in fonts_after}

    for font in shared_fonts:
        ttfont = TTFont(fonts_before[font]['filename'])
        glyphs_all['glyphs_all']['tests'].append({
            'font_before': fonts_before[font],
            'font_after': fonts_after[font],
            'glyphs': font_glyph_palette(ttfont)
        })
    return glyphs_all

