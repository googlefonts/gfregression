import io
import os
import re
import shutil
import sys
import tempfile
import types
import unittest
from unittest import mock

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(TESTS_DIR, ".."))
LIB_DIR = os.path.join(REPO_ROOT, "Lib")
APP_DIR = os.path.join(REPO_ROOT, "app")
if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

try:
    import diffenator  # noqa: F401
except ModuleNotFoundError:
    from fontTools.ttLib import TTFont

    class _FallbackDFont:
        def __init__(self, path):
            self.ttfont = TTFont(path)
            self.is_variable = "fvar" in self.ttfont

    sys.modules["diffenator"] = types.ModuleType("diffenator")
    sys.modules["diffenator.font"] = types.ModuleType("diffenator.font")
    sys.modules["diffenator.font"].DFont = _FallbackDFont
    sys.modules["diffenator.diff"] = types.ModuleType("diffenator.diff")
    sys.modules["diffenator.diff"].DiffFonts = mock.MagicMock()
    sys.modules["diffenator.dump"] = types.ModuleType("diffenator.dump")
    sys.modules["diffenator.dump"].dump_glyphs = mock.MagicMock()

import gfregression
from gfregression import downloadfonts


class _MockUploadedFile:
    def __init__(self, filename, data=b"fontbytes", fail_on_save=False):
        self.filename = filename
        self.data = data
        self.fail_on_save = fail_on_save

    def save(self, dst):
        if self.fail_on_save:
            raise OSError("Simulated save failure")
        with open(dst, "wb") as fh:
            fh.write(self.data)


def _install_main_dependencies():
    if "rethinkdb" not in sys.modules:
        rdb_mod = types.ModuleType("rethinkdb")
        rdb_errors = types.ModuleType("rethinkdb.errors")

        class _RqlDriverError(Exception):
            pass

        rdb_errors.RqlDriverError = _RqlDriverError
        rdb_mod.errors = rdb_errors
        rdb_mod.connect = mock.MagicMock()
        rdb_mod.table = mock.MagicMock()
        sys.modules["rethinkdb"] = rdb_mod
        sys.modules["rethinkdb.errors"] = rdb_errors

    if "init_db" not in sys.modules:
        init_db_mod = types.ModuleType("init_db")
        init_db_mod.build_tables = mock.MagicMock()
        sys.modules["init_db"] = init_db_mod

    if "utils" not in sys.modules:
        utils_mod = types.ModuleType("utils")
        utils_mod.browser_supports_vfs = mock.MagicMock(return_value=True)
        utils_mod.secret = lambda key: "test-secret"
        sys.modules["utils"] = utils_mod

    try:
        import flask  # noqa: F401
    except ModuleNotFoundError:
        flask_mod = types.ModuleType("flask")
        flask_request = types.SimpleNamespace(path="", form={}, files=None, args={}, user_agent=types.SimpleNamespace(string=""))
        flask_g = types.SimpleNamespace(rdb_conn=mock.MagicMock())

        class _FileList:
            def __init__(self, mapping):
                self._mapping = mapping

            def getlist(self, key):
                return list(self._mapping.get(key, []))

        class _UploadedStreamFile:
            def __init__(self, stream, filename):
                self._stream = stream
                self.filename = filename

            def save(self, dst):
                data = self._stream.read()
                with open(dst, "wb") as fh:
                    fh.write(data)

        class _Response:
            def __init__(self, data, status_code=200):
                if isinstance(data, str):
                    self.data = data.encode("utf-8")
                else:
                    self.data = data
                self.status_code = status_code

        class _Redirect(_Response):
            def __init__(self, location, code=302):
                super().__init__(b"", status_code=code)
                self.location = location

        class _TestClient:
            def __init__(self, app):
                self._app = app

            def post(self, path, data=None, content_type=None):
                data = data or {}
                form = {}
                files = {}
                for k, v in data.items():
                    items = v if isinstance(v, list) else [v]
                    for item in items:
                        if isinstance(item, tuple) and len(item) == 2 and hasattr(item[0], "read"):
                            files.setdefault(k, []).append(_UploadedStreamFile(item[0], item[1]))
                        else:
                            form[k] = item
                flask_request.path = path
                flask_request.form = form
                flask_request.files = _FileList(files)
                handler, kwargs = self._app._match_route(path)
                try:
                    rv = handler(**kwargs)
                except Exception:
                    if self._app.testing:
                        raise
                    err_handler = self._app._error_handlers.get(500)
                    if err_handler:
                        rv = err_handler(None)
                        if isinstance(rv, tuple):
                            return _Response(rv[0], rv[1])
                        return _Response(rv, 500)
                    raise
                if isinstance(rv, _Response):
                    return rv
                if isinstance(rv, tuple):
                    return _Response(rv[0], rv[1])
                return _Response(rv, 200)

        class _FallbackFlask:
            def __init__(self, import_name, static_url_path="/static"):
                self.import_name = import_name
                self.static_url_path = static_url_path
                self.testing = False
                self._routes = []
                self._error_handlers = {}

            def route(self, rule, methods=None, defaults=None):
                def decorator(func):
                    self._routes.append((rule, func, defaults or {}))
                    return func
                return decorator

            def before_request(self, func):
                return func

            def teardown_request(self, func):
                return func

            def errorhandler(self, code):
                def decorator(func):
                    self._error_handlers[code] = func
                    return func
                return decorator

            def _match_route(self, path):
                for rule, func, defaults in self._routes:
                    if rule == path:
                        return func, dict(defaults)
                    pattern = "^" + re.sub(r"<([^>]+)>", r"(?P<\1>[^/]+)", rule) + "$"
                    m = re.match(pattern, path)
                    if m:
                        kwargs = dict(defaults)
                        kwargs.update(m.groupdict())
                        return func, kwargs
                raise LookupError("No route for {}".format(path))

            def test_client(self):
                return _TestClient(self)

        flask_mod.Flask = _FallbackFlask
        flask_mod.g = flask_g
        flask_mod.request = flask_request
        flask_mod.render_template = lambda tpl, **kw: tpl
        flask_mod.redirect = lambda loc, code=302: _Redirect(loc, code=code)
        flask_mod.url_for = lambda endpoint, **kw: "/{}/{}".format(endpoint, kw.get("uuid", ""))
        flask_mod.send_file = lambda *a, **kw: _Response(b"")
        sys.modules["flask"] = flask_mod

        werkzeug_mod = types.ModuleType("werkzeug")
        werkzeug_ua = types.ModuleType("werkzeug.useragents")

        class _FallbackUserAgent:
            def __init__(self, ua_str):
                self.string = ua_str

        werkzeug_ua.UserAgent = _FallbackUserAgent
        werkzeug_mod.useragents = werkzeug_ua
        sys.modules["werkzeug"] = werkzeug_mod
        sys.modules["werkzeug.useragents"] = werkzeug_ua


class TestUserUploadSecurity(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.fonts_dir = os.path.join(self.root, "static", "fonts")
        self.templates_dir = os.path.join(self.root, "templates")
        os.makedirs(self.fonts_dir)
        os.makedirs(self.templates_dir)
        self.error_html = os.path.join(self.templates_dir, "error.html")
        with open(self.error_html, "wb") as fh:
            fh.write(b"ORIGINAL_ERROR_TEMPLATE")

        roboto_dir = os.path.join(TESTS_DIR, "data", "Roboto")
        with open(os.path.join(roboto_dir, "Roboto-Regular.ttf"), "rb") as fh:
            self.roboto_regular = fh.read()
        with open(os.path.join(roboto_dir, "Roboto-Bold.ttf"), "rb") as fh:
            self.roboto_bold = fh.read()
        with open(os.path.join(TESTS_DIR, "data", "Cabin", "Cabin-VF.ttf"), "rb") as fh:
            self.cabin_vf = fh.read()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_poc_traversal_and_abort_rejected_user_upload(self):
        files = [
            _MockUploadedFile("../../templates/error.html", b"PWNED_SSTI"),
            _MockUploadedFile("/nonexistent_poc_dir/x.ttf", b"x"),
        ]
        with self.assertRaises(ValueError):
            downloadfonts.user_upload(files, self.fonts_dir)
        with open(self.error_html, "rb") as fh:
            self.assertEqual(fh.read(), b"ORIGINAL_ERROR_TEMPLATE")
        self.assertEqual(os.listdir(self.fonts_dir), [])

    def test_poc_traversal_and_abort_rejected_family_from_user_upload(self):
        files = [
            _MockUploadedFile("../../templates/error.html", b"PWNED_SSTI"),
            _MockUploadedFile("/nonexistent_poc_dir/x.ttf", b"x"),
        ]
        with self.assertRaises(ValueError):
            gfregression.family_from_user_upload(files, self.fonts_dir)
        with open(self.error_html, "rb") as fh:
            self.assertEqual(fh.read(), b"ORIGINAL_ERROR_TEMPLATE")
        self.assertEqual(os.listdir(self.fonts_dir), [])

    def test_invalid_and_traversal_filenames_rejected(self):
        bad_filenames = [
            "../evil.ttf",
            "..\\..\\evil.ttf",
            "/etc/passwd",
            "/tmp/evil.ttf",
            "Roboto.ttf\x00.html",
            "error.html",
            "evil.ttf.html",
            "",
            None,
            ".ttf",
            ".hidden.ttf",
            "..ttf",
            "foo..ttf",
            "Roboto-Regular\n.ttf",
            "Roboto-</style><script>.ttf",
            "CON.ttf",
        ]
        for bad_name in bad_filenames:
            with self.subTest(filename=bad_name):
                with self.assertRaises(ValueError):
                    downloadfonts.user_upload([_MockUploadedFile(bad_name)], self.fonts_dir)
        self.assertEqual(os.listdir(self.fonts_dir), [])

    def test_filename_length_limit(self):
        for too_long in ("A" * 252 + ".ttf", "A" * 300 + ".ttf"):
            with self.subTest(length=len(too_long)):
                with self.assertRaises(ValueError):
                    downloadfonts.user_upload([_MockUploadedFile(too_long)], self.fonts_dir)
        self.assertEqual(os.listdir(self.fonts_dir), [])

        max_ok = "A" * 251 + ".ttf"
        self.assertEqual(len(max_ok), 255)
        saved = downloadfonts.user_upload([_MockUploadedFile(max_ok, self.roboto_regular)], self.fonts_dir)
        self.assertEqual(len(saved), 1)
        self.assertEqual(os.path.basename(saved[0]), max_ok)

    def test_symlink_escape_rejected(self):
        outside_file = os.path.join(self.root, "outside.txt")
        with open(outside_file, "wb") as fh:
            fh.write(b"SENSITIVE")
        symlink_path = os.path.join(self.fonts_dir, "Roboto-Regular.ttf")
        os.symlink(outside_file, symlink_path)

        with self.assertRaises(ValueError):
            downloadfonts.user_upload(
                [_MockUploadedFile("Roboto-Regular.ttf", b"OVERWRITE")],
                self.fonts_dir,
            )
        with open(outside_file, "rb") as fh:
            self.assertEqual(fh.read(), b"SENSITIVE")

    def test_preexisting_file_protected(self):
        existing_path = os.path.join(self.fonts_dir, "Roboto-Regular.ttf")
        with open(existing_path, "wb") as fh:
            fh.write(b"PREEXISTING")

        files = [
            _MockUploadedFile("Roboto-Regular.ttf", b"NEW"),
            _MockUploadedFile("Roboto-Bold.ttf", b"X", fail_on_save=True),
        ]
        with self.assertRaises(ValueError):
            downloadfonts.user_upload(files, self.fonts_dir)
        with open(existing_path, "rb") as fh:
            self.assertEqual(fh.read(), b"PREEXISTING")

    def test_batch_rollback_on_save_error(self):
        files = [
            _MockUploadedFile("Roboto-Regular.ttf", self.roboto_regular),
            _MockUploadedFile("Roboto-Bold.ttf", self.roboto_bold, fail_on_save=True),
        ]
        with self.assertRaises(OSError):
            downloadfonts.user_upload(files, self.fonts_dir)
        self.assertEqual(os.listdir(self.fonts_dir), [])

    def test_duplicate_filenames_rejected(self):
        for pair in (
            ("Roboto-Regular.ttf", "Roboto-Regular.ttf"),
            ("Roboto-Regular.ttf", "roboto-regular.ttf"),
        ):
            with self.subTest(pair=pair):
                files = [
                    _MockUploadedFile(pair[0], self.roboto_regular),
                    _MockUploadedFile(pair[1], self.roboto_regular),
                ]
                with self.assertRaises(ValueError):
                    downloadfonts.user_upload(files, self.fonts_dir)
                self.assertEqual(os.listdir(self.fonts_dir), [])

    def test_valid_static_upload_relative_dst(self):
        orig_cwd = os.getcwd()
        os.chdir(self.root)
        try:
            rel_fonts_dir = os.path.join("static", "fonts")
            files = [
                _MockUploadedFile("Roboto-Regular.ttf", self.roboto_regular),
                _MockUploadedFile("Roboto-Bold.ttf", self.roboto_bold),
            ]
            family = gfregression.family_from_user_upload(files, rel_fonts_dir)
            self.assertEqual(family.name, "Roboto")
            self.assertEqual(len(family.fonts), 2)

            saved_files = os.listdir(self.fonts_dir)
            self.assertEqual(len(saved_files), 2)
            for fname in saved_files:
                self.assertTrue(fname.endswith(".ttf"))
                self.assertNotIn("Roboto", fname)
            for font in family.fonts:
                self.assertTrue(font.path.startswith("static/fonts/") or font.path.startswith(rel_fonts_dir))
                self.assertIn("url(/static/fonts/", font.css_font_face.replace(os.sep, "/"))
        finally:
            os.chdir(orig_cwd)

    def test_uppercase_ttf_and_otf_allowed(self):
        saved = downloadfonts.user_upload(
            [
                _MockUploadedFile("Roboto-Regular.TTF", self.roboto_regular),
                _MockUploadedFile("Roboto-Regular.otf", b"OTTOdummy"),
            ],
            self.fonts_dir,
        )
        self.assertEqual(len(saved), 2)
        basenames = sorted(os.path.basename(p) for p in saved)
        self.assertEqual(basenames, ["Roboto-Regular.otf", "Roboto-Regular.ttf"])

    def test_variable_font_brackets_preserved(self):
        files = [_MockUploadedFile("Cabin[wdth,wght].ttf", self.cabin_vf)]
        family = gfregression.family_from_user_upload(files, self.fonts_dir)
        self.assertEqual(family.name, "Cabin")
        self.assertTrue(family.has_vfs)

    def test_partial_failure_rollback_in_family_from_user_upload(self):
        files = [
            _MockUploadedFile("Roboto-Regular.ttf", self.roboto_regular),
            _MockUploadedFile("Roboto-Bold.ttf", b"not-a-valid-ttf"),
        ]
        with self.assertRaises(ValueError):
            gfregression.family_from_user_upload(files, self.fonts_dir)
        self.assertEqual(os.listdir(self.fonts_dir), [])

    def test_mismatched_families_rejected_with_cleanup(self):
        files = [
            _MockUploadedFile("Roboto-Regular.ttf", self.roboto_regular),
            _MockUploadedFile("Cabin[wdth,wght].ttf", self.cabin_vf),
        ]
        with self.assertRaises(ValueError):
            gfregression.family_from_user_upload(files, self.fonts_dir)
        self.assertEqual(os.listdir(self.fonts_dir), [])


class TestUploadFontsEndpoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _install_main_dependencies()
        import main as main_mod
        cls.main_mod = main_mod

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.fonts_dir = os.path.join(self.root, "static", "fonts")
        self.templates_dir = os.path.join(self.root, "templates")
        os.makedirs(self.fonts_dir)
        os.makedirs(self.templates_dir)
        self.error_html = os.path.join(self.templates_dir, "error.html")
        with open(self.error_html, "wb") as fh:
            fh.write(b"ORIGINAL_ERROR_TEMPLATE")

        with open(os.path.join(TESTS_DIR, "data", "Roboto", "Roboto-Regular.ttf"), "rb") as fh:
            self.roboto_regular = fh.read()

        self._orig_fonts_dir = self.main_mod.FONTS_DIR
        self._orig_testing = self.main_mod.app.testing
        self._orig_diff_families = self.main_mod.DIFF_FAMILIES
        self.main_mod.FONTS_DIR = self.fonts_dir
        self.main_mod.app.testing = True
        self.client = self.main_mod.app.test_client()

    def tearDown(self):
        self.main_mod.FONTS_DIR = self._orig_fonts_dir
        self.main_mod.app.testing = self._orig_testing
        self.main_mod.DIFF_FAMILIES = self._orig_diff_families
        shutil.rmtree(self.root, ignore_errors=True)

    def test_unknown_upload_type_returns_400(self):
        resp_api = self.client.post("/api/upload/unknown", data={})
        self.assertEqual(resp_api.status_code, 400)

        resp_web = self.client.post("/upload-fonts", data={"fonts": "unknown"})
        self.assertEqual(resp_web.status_code, 400)
        self.assertEqual(os.listdir(self.fonts_dir), [])

    def test_traversal_upload_returns_400_and_preserves_files(self):
        resp = self.client.post(
            "/api/upload/user",
            data={
                "fonts_after": [
                    (io.BytesIO(b"PWNED_SSTI"), "../../templates/error.html"),
                    (io.BytesIO(b"x"), "/nonexistent/x.ttf"),
                ],
                "fonts_before": [
                    (io.BytesIO(self.roboto_regular), "Roboto-Regular.ttf"),
                ],
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(resp.status_code, 400)
        with open(self.error_html, "rb") as fh:
            self.assertEqual(fh.read(), b"ORIGINAL_ERROR_TEMPLATE")
        self.assertEqual(os.listdir(self.fonts_dir), [])

    def test_overlong_filename_returns_400(self):
        resp = self.client.post(
            "/api/upload/user",
            data={
                "fonts_after": [
                    (io.BytesIO(self.roboto_regular), "A" * 300 + ".ttf"),
                ],
                "fonts_before": [
                    (io.BytesIO(self.roboto_regular), "Roboto-Regular.ttf"),
                ],
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(os.listdir(self.fonts_dir), [])

    def test_user_upload_second_step_failure_cleans_up_first_family(self):
        resp_empty = self.client.post(
            "/api/upload/user",
            data={
                "fonts_after": [
                    (io.BytesIO(self.roboto_regular), "Roboto-Regular.ttf"),
                ],
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(resp_empty.status_code, 400)
        self.assertEqual(os.listdir(self.fonts_dir), [])

        resp_corrupt = self.client.post(
            "/api/upload/user",
            data={
                "fonts_after": [
                    (io.BytesIO(self.roboto_regular), "Roboto-Regular.ttf"),
                ],
                "fonts_before": [
                    (io.BytesIO(b"not-a-valid-ttf"), "Roboto-Regular.ttf"),
                ],
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(resp_corrupt.status_code, 400)
        self.assertEqual(os.listdir(self.fonts_dir), [])

    def test_googlefonts_upload_failure_cleans_up_first_family(self):
        with mock.patch.object(
            self.main_mod,
            "family_from_googlefonts",
            side_effect=RuntimeError("GF API error"),
        ):
            with self.assertRaises(RuntimeError):
                self.client.post(
                    "/api/upload/googlefonts",
                    data={
                        "fonts_after": [
                            (io.BytesIO(self.roboto_regular), "Roboto-Regular.ttf"),
                        ],
                    },
                    content_type="multipart/form-data",
                )
        self.assertEqual(os.listdir(self.fonts_dir), [])

    def test_valid_user_upload_succeeds(self):
        self.main_mod.DIFF_FAMILIES = False
        with mock.patch.object(self.main_mod.r, "table", return_value=mock.MagicMock()):
            resp = self.client.post(
                "/api/upload/user",
                data={
                    "fonts_after": [
                        (io.BytesIO(self.roboto_regular), "Roboto-Regular.ttf"),
                    ],
                    "fonts_before": [
                        (io.BytesIO(self.roboto_regular), "Roboto-Regular.ttf"),
                    ],
                },
                content_type="multipart/form-data",
            )
        self.assertEqual(resp.status_code, 302)
        saved_files = os.listdir(self.fonts_dir)
        self.assertEqual(len(saved_files), 2)
        for fname in saved_files:
            self.assertTrue(fname.endswith(".ttf"))
            self.assertNotIn("Roboto", fname)


if __name__ == "__main__":
    unittest.main()
