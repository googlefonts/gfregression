# -*- coding: utf-8 -*-
from flask import Flask, g, request, render_template, redirect, url_for
from werkzeug.useragents import UserAgent
from uuid import uuid4
import os
import json
import rethinkdb as r
from rethinkdb.errors import RqlDriverError
import family

import init_db
from settings import DIFF_LIMIT, VIEWS, MEDIA_DIR
from utils import browser_supports_vfs


__version__ = 2.101

app = Flask(__name__, static_url_path='/static')

RDB_HOST = os.environ.get('RDB_HOST') or 'localhost'
RDB_PORT = os.environ.get('RDB_PORT') or 28015
DB = 'diffenator_web'

init_db.build_tables(host=RDB_HOST, port=RDB_PORT, db=DB)


@app.before_request
def before_request():
    try:
        g.rdb_conn = r.connect(host=RDB_HOST, port=RDB_PORT, db=DB)
    except RqlDriverError:
        abort(503, "No database connection could be established.")


@app.teardown_request
def teardown_request(exception):
    try:
        g.rdb_conn.close()
    except AttributeError:
        pass


@app.route('/')
def index():
    return render_template('upload.html')


@app.route("/api/upload/<upload_type>", methods=['POST'])
@app.route('/upload-fonts', methods=["POST"])
def upload_fonts(upload_type=None):
    """Upload fonts to diff."""
    from_api = False
    if 'api' in request.path:
        upload_type = upload_type
        from_api = True
    else:
        upload_type = request.form.get('fonts')

    # try:
    if upload_type == 'googlefonts':
        family_after = family.from_user_upload(request.files.getlist('fonts_after'))
        family_before = family.from_googlefonts(family_after.name)
    elif upload_type == 'user':
        family_after = family.from_user_upload(request.files.getlist('fonts_after'))
        family_before = family.from_user_upload(request.files.getlist('fonts_before'))
    # TODO (M Foley) get fonts from a github dir
    uuid = str(uuid4())

    diff_families = family.diff_families(family_before, family_after, uuid)
    for diff in diff_families:
        r.table('families_diffs').insert(diff).run(g.rdb_conn)
    families = family.get_families(family_before, family_after, uuid)
    r.table('families').insert(families).run(g.rdb_conn)
    # except Exception, e:
    #     return json.dumps({'error': str(e)})
    if from_api:
        return redirect(url_for("api_uuid_info", uuid=uuid))
    return redirect(url_for("compare", view='glyphs_new', uuid=uuid))


@app.route('/screenshot/<uuid>/<view>/<font_position>/<font_size>')
@app.route('/screenshot/<uuid>/<view>/<font_position>',
           defaults={'font_size': 60})
@app.route('/compare/<uuid>/<view>/<font_size>')
@app.route('/compare/<uuid>', defaults={"view": "glyphs_new", "font_size": 60})
def compare(uuid, view, font_size, font_position='before'):
    families = list(r.table('families')
        .filter({'uuid': uuid}).run(g.rdb_conn))[0]
    families_diffs = list(r.table('families_diffs')
        .filter({'uuid': uuid, 'view': view}).run(g.rdb_conn))

    user_agent = UserAgent(request.user_agent.string)
    if families['has_vfs'] and not browser_supports_vfs(user_agent):
        raise Exception("Browser does not support variable fonts!")

    if not families_diffs and view not in ['editor', 'waterfall']:
        return render_template('404.html'), 404

    if 'screenshot' in request.path:
        html_page = "screenshot.html"
    else:
        html_page = "test_fonts.html"

    return render_template(
        html_page,
        family=families,
        font_diffs=families_diffs,
        font_position=font_position,
        limit=DIFF_LIMIT,
        view=view,
        views=VIEWS,
        uuid=uuid,
        font_size=int(font_size)
    )


@app.route("/api/info/<uuid>")
def api_uuid_info(uuid):
    """Return info regarding a diff"""
    families = list(r.table('families')
                 .filter({'uuid': uuid}).run(g.rdb_conn))[0]
    families_diffs = list(r.table('families_diffs')
        .filter({'uuid': uuid}).run(g.rdb_conn))

    changed = set({})
    for diff in families_diffs:
        if len(diff['items']) != 0:
            changed.add(diff['view'])

    return json.dumps({
        'uuid': uuid,
        'fonts': families['styles'],
        'diffs': list(changed),
        'has_vfs': families['has_vfs']
    })


@app.route("/api/upload-media", methods=['POST'])
def upload_media():
    """Media upload end point"""
    if 'uuid' not in request.form:
        raise Exception('No uuid specified')
    uuid = request.form['uuid']
    uploaded_files = request.files.getlist('files')
    media_dir = os.path.join(MEDIA_DIR, uuid)
    if not os.path.isdir(media_dir):
        os.mkdir(media_dir)
    paths = []
    for f in uploaded_files:
        destination = os.path.join(media_dir, f.filename)
        f.save(destination)
        paths.append(destination)
    return json.dumps({'items': paths})


@app.errorhandler(500)
def internal_error(error):
    import traceback
    return render_template(
        "error.html",
        traceback=traceback.format_exc()
    )


@app.errorhandler(404)
def not_found(error):
    return render_template(
        "404.html"), 404


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
