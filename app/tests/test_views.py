import os
import unittest
import requests
from main import app


class TestApiEndPoints(unittest.TestCase):
    # TODO make test run from test_client, not through live server
    def setUp(self):
        app.config['testing'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()
        self.local_base_url = 'http://127.0.0.1:5000'

    def test_api_retrieve_fonts_gf_upload(self):
        """Test we can upload fonts via the /upload/googlefonts endpoint.

        This endpoint will retrieve a set of fonts from the user and a set
        from Googlefonts if it exists"""
        url = self.local_base_url + '/api/upload/googlefonts'
        # TODO make local
        fonts = [
            os.path.join(os.path.dirname(__file__), 'data', 'Roboto-Regular.ttf'),
            os.path.join(os.path.dirname(__file__), 'data', 'Roboto-Bold.ttf'),
        ]
        payload = [('fonts', open(f, 'rb')) for f in fonts]
        request = requests.post(url, files=payload)
        self.assertEqual(request.status_code, 200)

    def test_api_retrieve_fonts_user_upload(self):
        """Test we can upload fonts via the /upload/user endpoint.

        this endpoint will retrieve two sets of fonts from a user."""
        url = self.local_base_url + '/api/upload/user'
        # TODO make local
        fonts = [
            os.path.join(os.path.dirname(__file__), 'data', 'Roboto-Regular.ttf'),
            os.path.join(os.path.dirname(__file__), 'data', 'Roboto-Bold.ttf'),
        ]
        fonts2 = fonts
        payload = [('fonts', open(f, 'rb')) for f in fonts] + \
                  [('fonts2', open(f, 'rb')) for f in fonts2]
        request = requests.post(url, files=payload)
        self.assertEqual(request.status_code, 200)


if __name__ == '__main__':
    unittest.main()
