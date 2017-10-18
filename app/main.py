'''
Compare local fonts against fonts available on fonts.google.com
'''
from __future__ import print_function
from flask import Flask, request, render_template, redirect, url_for
from uuid import uuid4
import os
import json

import retrievefonts
from comparefonts import CompareFonts
from settings import BASE_FONTS_PATH, TARGET_FONTS_PATH
from utils import (
    get_fonts,
    delete_fonts,
    equalize_font_sets
)

__version__ = 1.200

app = Flask(__name__, static_url_path='/static')

with open('./dummy_text.txt', 'r') as dummy_text_file:
    dummy_text = dummy_text_file.read()


@app.route('/')
def index():
    return render_template('upload.html')


@app.route('/retrieve-fonts', methods=["POST"])
def retrieve_fonts():
    delete_fonts(TARGET_FONTS_PATH)
    delete_fonts(BASE_FONTS_PATH)
    """Upload/download the two sets of fonts to compare"""
    form = request.form
    # Create a unique "session ID" for this particular session.
    session_id = str(uuid4())
    target_fonts_path = os.path.join(TARGET_FONTS_PATH, session_id)
    base_fonts_path = os.path.join(BASE_FONTS_PATH, session_id)

    # # Is the upload using Ajax, or a direct POST by the form?
    is_ajax = True if form.get("__ajax", None) == "true" else False

    # User wants to compare fonts against GF hosted.
    if form.get('fonts') == 'from_gf':
        retrievefonts.user_upload(request, "target_fonts", target_fonts_path)
        families = [f for f in os.listdir(target_fonts_path)]
        retrievefonts.google_fonts(base_fonts_path, families)

    # User wants to compare upstream github fonts against GF hosted.
    elif form.get('fonts') == 'from_github_url':
        retrievefonts.github_dir(form.get('github-url'), target_fonts_path)
        families = [f for f in os.listdir(target_fonts_path)]
        retrievefonts.google_fonts(base_fonts_path, families)

    # User wants to compare two sets of local fonts.
    elif form.get('fonts') == 'from_local':
        retrievefonts.user_upload(request, "target_fonts", target_fonts_path)
        retrievefonts.user_upload(request, "base_fonts", base_fonts_path)

    if is_ajax:
        return ajax_response(True, session_id)
    return redirect(url_for("compare_fonts", uuid=session_id))


def ajax_response(status, msg):
    status_code = "ok" if status else "error"
    return json.dumps(dict(
        status=status_code,
        msg=msg,
    ))


@app.route("/compare/<uuid>")
def compare_fonts(uuid):

    base_fonts_path = os.path.join(BASE_FONTS_PATH, uuid)
    base_fonts = get_fonts(base_fonts_path, 'base')

    target_fonts_path = os.path.join(TARGET_FONTS_PATH, uuid)
    target_fonts = get_fonts(target_fonts_path, 'target')

    equalize_font_sets(base_fonts, target_fonts)
    compare_fonts = CompareFonts(base_fonts, target_fonts)

    # css hook to swap remote fonts to local fonts and vice versa
    to_target_fonts = ','.join([i.cssname for i in target_fonts])
    to_base_fonts = ','.join([i.cssname for i in base_fonts])

    return render_template(
        'test_fonts.html',
        dummy_text=dummy_text,
        target_fonts=target_fonts,
        base_fonts=base_fonts,
        grouped_fonts=zip(target_fonts, base_fonts),
        changed_glyphs=compare_fonts.inconsistent_glyphs(),
        new_glyphs=compare_fonts.new_glyphs(),
        missing_glyphs=compare_fonts.missing_glyphs(),
        languages=compare_fonts.languages(),
        to_target_fonts=to_target_fonts,
        to_base_fonts=to_base_fonts
    )


@app.route("/api/upload", methods=['POST'])
def api_retrieve_fonts():
    """Upload a font via the api.
    Caveat, compatible only for GoogleFonts at the moment"""
    delete_fonts(TARGET_FONTS_PATH)
    delete_fonts(BASE_FONTS_PATH)
    session_id = str(uuid4())
    target_fonts_path = os.path.join(TARGET_FONTS_PATH, session_id)
    base_fonts_path = os.path.join(BASE_FONTS_PATH, session_id)

    retrievefonts.user_upload(request, "fonts", target_fonts_path)
    families = [f for f in os.listdir(target_fonts_path)]
    retrievefonts.google_fonts(base_fonts_path, families)

    targetfonts_url = url_for("screenshot_comparison", uuid=session_id)
    return targetfonts_url


@app.route("/screenshot/<uuid>")
def screenshot_comparison(uuid):
    target_fonts_path = os.path.join(TARGET_FONTS_PATH, uuid)
    target_fonts = get_fonts(target_fonts_path, 'target')

    return render_template(
        'screenshot.html',
        dummy_text=dummy_text,
        target_fonts=target_fonts,
    )

if __name__ == "__main__":
    app.run(debug=True)
