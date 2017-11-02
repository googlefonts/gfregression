import unittest
import requests
from app.main import app


class TestApiEndPoints(unittest.TestCase):
    # TODO make test run from test_client, not through live server
    def setUp(self):
        app.config['testing'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()

    def test_view_api_retrieve_fonts(self):
        """Test we can upload fonts via the /upload endpoint"""
        url_gfregression = 'http://127.0.0.1:5000'
        url_upload = url_gfregression + '/api/upload'
        # TODO make local
        fonts = [
            '/Users/marc/Documents/gfregression/app/tests/data/Roboto-Regular.ttf',
            '/Users/marc/Documents/gfregression/app/tests/data/Roboto-Bold.ttf',
        ]
        payload = [('fonts', open(f, 'rb')) for f in fonts]
        request = requests.post(url_upload, files=payload)
        self.assertEqual(request.status_code, 200)


if __name__ == '__main__':
    unittest.main()