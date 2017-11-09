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
from comparefonts import CompareFonts
from settings import BASE_FONTS_PATH, TARGET_FONTS_PATH

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
    fonts = fontmanager.new()
    # # Is the upload using Ajax, or a direct POST by the form?
    form = request.form
    is_ajax = True if form.get("__ajax", None) == "true" else False

    # User wants to compare fonts against GF hosted.
    if form.get('fonts') == 'from_gf':
        downloadfonts.user_upload(request, "target_fonts", fonts.target_dir)
        families = os.listdir(fonts.target_dir)
        downloadfonts.google_fonts(fonts.base_dir, families)

    # User wants to compare upstream github fonts against GF hosted.
    elif form.get('fonts') == 'from_github_url':
        downloadfonts.github_dir(form.get('github-url'), fonts.target_dir)
        families = os.listdir(fonts.target_dir)
        downloadfonts.google_fonts(fonts.base_dir, families)

    # User wants to compare two sets of local fonts.
    elif form.get('fonts') == 'from_local':
        downloadfonts.user_upload(request, "target_fonts", fonts.target_dir)
        downloadfonts.user_upload(request, "base_fonts", fonts.base_dir)

    fonts.equalize_fonts()

    if is_ajax:
        return ajax_response(True, fonts.uid)
    return redirect(url_for("compare_fonts", uid=fonts.uid))


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
    fonts = fontmanager.load(uid)
    compare_fonts = CompareFonts(fonts.base_fonts, fonts.target_fonts)
    # css hook to swap remote fonts to local fonts and vice versa
    to_target_fonts = ','.join([i.cssname for i in fonts.target_fonts])
    to_base_fonts = ','.join([i.cssname for i in fonts.base_fonts])

    return render_template(
        'test_fonts.html',
        dummy_text=dummy_text,
        target_fonts=fonts.target_fonts,
        base_fonts=fonts.base_fonts,
        grouped_fonts=zip(fonts.target_fonts, fonts.base_fonts),
        changed_glyphs=compare_fonts.inconsistent_glyphs(),
        new_glyphs=compare_fonts.new_glyphs(),
        missing_glyphs=compare_fonts.missing_glyphs(),
        languages=compare_fonts.languages(),
        to_target_fonts=to_target_fonts,
        to_base_fonts=to_base_fonts
    )


@app.route("/api/upload", methods=['POST'])
def api_retrieve_fonts():
    """Upload fonts via the api.
    Caveat, compatible only for GoogleFonts at the moment"""
    fonts = fontmanager.new()

    downloadfonts.user_upload(request, "fonts", fonts.target_dir)
    families = os.listdir(fonts.target_dir)
    downloadfonts.google_fonts(fonts.base_dir, families)

    fonts.equalize_fonts()

    return json.dumps({'uid': fonts.uid})


@app.route("/screenshot/<page>/<uuid>/<font_dir>")
def screenshot_comparison(page, uuid, font_dir):
    pages = {
        'waterfall': 'page-waterfall.html',
        'glyphs-modified': 'page-glyphs-modified.html',
        'glyphs-new': 'page-glyphs-new.html',
        'glyphs-missing': 'page-glyphs-missing.html',
    }

    fonts = fontmanager.load(uuid)
    compare_fonts = CompareFonts(fonts.base_fonts, fonts.target_fonts)
    fonts = fonts.base_fonts if font_dir == 'basefonts' else fonts.target_fonts
    fonts_type = 'Google Fonts' if font_dir == 'basefonts' else 'New Fonts'
    return render_template(
        'screenshot.html',
        dummy_text=dummy_text,
        target_fonts=fonts,
        changed_glyphs=compare_fonts.inconsistent_glyphs(),
        new_glyphs=compare_fonts.new_glyphs(),
        missing_glyphs=compare_fonts.missing_glyphs(),
        page_to_load=pages[page],
        fonts_type=fonts_type
    )


if __name__ == "__main__":
    app.run(debug=True)
