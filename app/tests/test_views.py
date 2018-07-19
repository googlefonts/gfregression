import os
import unittest
import requests
from main import app
from utils import browser_supports_vfs
from werkzeug.useragents import UserAgent


class TestApiEndPoints(unittest.TestCase):
    # TODO make test run from test_client, not through live server
    def setUp(self):
        self.local_base_url = 'http://127.0.0.1:5000'

    def test_api_upload_fonts_gf_upload(self):
        """Test we can upload fonts via the /upload/googlefonts endpoint.

        This endpoint will retrieve a set of fonts from the user and a set
        from Googlefonts if it exists"""
        url = self.local_base_url + '/api/upload/googlefonts'
        # TODO make local
        fonts = [
            os.path.join(os.path.dirname(__file__), 'data', 'Roboto-Regular.ttf'),
            os.path.join(os.path.dirname(__file__), 'data', 'Roboto-Bold.ttf'),
        ]
        payload = [('fonts_after', open(f, 'rb')) for f in fonts]
        request = requests.post(url, files=payload)
        self.assertEqual(request.status_code, 200)

    def test_api_upload_fonts_user_upload(self):
        """Test we can upload fonts via the /upload/user endpoint.

        this endpoint will retrieve two sets of fonts from a user."""
        url = self.local_base_url + '/api/upload/user'
        # TODO make local
        fonts = [
            os.path.join(os.path.dirname(__file__), 'data', 'Roboto-Regular.ttf'),
            os.path.join(os.path.dirname(__file__), 'data', 'Roboto-Bold.ttf'),
        ]
        fonts2 = fonts
        payload = [('fonts_before', open(f, 'rb')) for f in fonts] + \
                  [('fonts_after', open(f, 'rb')) for f in fonts2]
        request = requests.post(url, files=payload)
        self.assertEqual(request.status_code, 200)


class TestNonVFBrowser(unittest.TestCase):

    def setUp(self):
        self.mock_header_safari_vf_supported = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1.2 Safari/605.1.15'
        self.mock_header_safari_vf_not_supported = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/10.1.2 Safari/605.1.15'

    def test_non_vf_browser_cant_view_vf_diff(self):
        user_agent = UserAgent(self.mock_header_safari_vf_supported)
        self.assertEqual(browser_supports_vfs(user_agent), True)

        user_agent = UserAgent(self.mock_header_safari_vf_not_supported)
        self.assertEqual(browser_supports_vfs(user_agent), False)


if __name__ == '__main__':
    unittest.main()
