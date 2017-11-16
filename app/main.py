'''
Compare local fonts against fonts available on fonts.google.com
'''
from __future__ import print_function
from flask import Flask, request, render_template, redirect, url_for
from uuid import uuid4
import os
import json

import downloadfonts
import fontmanager
from glyphpalette import fonts_glyph_palettes
from comparefonts import CompareFonts

__version__ = 1.200

app = Flask(__name__, static_url_path='/static')

dummy_text_path = os.path.join(os.path.dirname(__file__), 'dummy_text.txt')
with open(dummy_text_path, 'r') as dummy_text_file:
    dummy_text = dummy_text_file.read()


@app.route('/')
def index():
    return render_template('upload.html')


@app.route('/retrieve-fonts', methods=["POST"])
def retrieve_fonts():
    """Upload/download the two sets of fonts to compare"""
    manager = fontmanager.new()
    # # Is the upload using Ajax, or a direct POST by the form?
    form = request.form
    is_ajax = True if form.get("__ajax", None) == "true" else False

    # User wants to compare fonts against GF hosted.
    if form.get('fonts') == 'from_gf':
        downloadfonts.user_upload(request, "fonts_after", manager.after_dir)
        families = os.listdir(manager.after_dir)
        downloadfonts.google_fonts(manager.before_dir, families)

    # User wants to compare upstream github fonts against GF hosted.
    elif form.get('fonts') == 'from_github_url':
        downloadfonts.github_dir(form.get('github-url'), manager.after_dir)
        families = os.listdir(manager.after_dir)
        downloadfonts.google_fonts(manager.before_dir, families)

    # User wants to compare two sets of local fonts.
    elif form.get('fonts') == 'from_local':
        downloadfonts.user_upload(request, "fonts_after", manager.after_dir)
        downloadfonts.user_upload(request, "fonts_before", manager.before_dir)

    manager.equalize_fonts()

    if is_ajax:
        return ajax_response(True, manager.uid)
    return redirect(url_for("compare_fonts", uid=manager.uid))


def ajax_response(status, msg):
    status_code = "ok" if status else "error"
    return json.dumps(dict(
        status=status_code,
        msg=msg,
    ))


@app.route("/compare/<uid>")
def compare_fonts(uid):
    if not fontmanager.has_fonts(uid):
        # TODO (M Foley) add 404 style html page
        return 'Fonts do not exist!'
    manager = fontmanager.load(uid)
    compare_fonts = CompareFonts(manager.fonts_before, manager.fonts_after)
    # css hook to swap remote fonts to local fonts and vice versa
    to_fonts_after = ','.join([i.css_name for i in manager.fonts_after])
    to_fonts_before = ','.join([i.css_name for i in manager.fonts_before])

    return render_template(
        'test_fonts.html',
        dummy_text=dummy_text,
        fonts_after=manager.fonts_after,
        fonts_before=manager.fonts_before,
        grouped_fonts=zip(manager.fonts_after, manager.fonts_before),
        changed_glyphs=compare_fonts.inconsistent_glyphs(),
        new_glyphs=compare_fonts.new_glyphs(),
        missing_glyphs=compare_fonts.missing_glyphs(),
        languages=compare_fonts.languages(),
        to_fonts_after=to_fonts_after,
        to_fonts_before=to_fonts_before
    )


@app.route("/api/upload/<upload_type>", methods=['POST'])
def api_retrieve_fonts(upload_type):
    """Upload fonts via the api."""
    manager = fontmanager.new()

    if upload_type == 'googlefonts':
        downloadfonts.user_upload(request, "fonts", manager.after_dir)
        families = os.listdir(manager.after_dir)
        downloadfonts.google_fonts(manager.before_dir, families)

    elif upload_type == 'user':
        downloadfonts.user_upload(request, "fonts", manager.after_dir)
        downloadfonts.user_upload(request, "fonts2", manager.before_dir)

    manager.equalize_fonts()

    return json.dumps({'uid': manager.uid})


@app.route("/screenshot/glyphs-all/<uuid>/<font_dir>/<pt_size>")
def screenshot_glyphs_all(uuid, font_dir, pt_size):
    """Screenshot view for all glyphs at a particular point size"""
    manager = fontmanager.load(uuid)
    font_to_display = manager.fonts_before if font_dir == 'before' else manager.fonts_after
    fonts_label = 'Before' if font_dir == 'before' else 'After'

    glyph_palettes = fonts_glyph_palettes(manager.fonts_before)
    return render_template(
        'screenshot.html',
        fonts_after=font_to_display,
        glyph_pallettes=glyph_palettes,
        page_to_load='page-glyphs-all.html',
        fonts_label=fonts_label,
        pt_size=int(pt_size),
    )


@app.route("/screenshot/<page>/<uuid>/<font_dir>")
def screenshot_comparison(page, uuid, font_dir):
    pages = {
        'waterfall': 'page-waterfall.html',
        'glyphs-modified': 'page-glyphs-modified.html',
        'glyphs-new': 'page-glyphs-new.html',
    }
    manager = fontmanager.load(uuid)
    font_to_display = manager.fonts_before if font_dir == 'before' else manager.fonts_after
    fonts_label = 'Before' if font_dir == 'before' else 'After'

    compare_fonts = CompareFonts(manager.fonts_before, manager.fonts_after)

    if page in pages:
        return render_template(
            'screenshot.html',
            dummy_text=dummy_text,
            fonts_after=font_to_display,
            changed_glyphs=compare_fonts.inconsistent_glyphs(),
            new_glyphs=compare_fonts.new_glyphs(),
            missing_glyphs=compare_fonts.missing_glyphs(),
            page_to_load=pages[page],
            fonts_label=fonts_label
        )
    else:
        return "Page does not exist. Choose from [%s]" % ', '.join(pages)


if __name__ == "__main__":
    app.run(debug=True)
