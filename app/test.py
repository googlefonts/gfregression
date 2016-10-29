import unittest
from main import (
    fonts_on_google,
    _font_exists,
    _convert_camelcase
    )


class GoogleFontsApi(unittest.TestCase):
    def setUp(self):
        self.fallback_url = 'https://fonts.googleapis.com/css?family=Inconsolata:400'

    def test_font_exists(self):
        self.assertEqual(_font_exists(self.fallback_url), True)

    def test_convert_camelcase(self):
        sngl_name = 'Anaheim'
        dbl_name = 'BadScript'
        self.assertEqual(_convert_camelcase(sngl_name, '+'), 'Anaheim')
        self.assertEqual(_convert_camelcase(dbl_name, '+'), 'Bad+Script')
        self.assertEqual(_convert_camelcase(dbl_name), 'Bad Script')

    def test_get_google_fontface_url_from_local_font(self):
        """Test we can convert a local font's path into a compatible url for
        the Google fonts api"""
        inconsolata_local = [('path/Inconsolata-Regular.ttf', 'Inconsolata-Regular')]

        self.assertEqual(fonts_on_google(inconsolata_local),
                         [('Inconsolata',
                           'Inconsolata',
                           '400',
                           'normal',
                           self.fallback_url)])


if __name__ == '__main__':
    unittest.main()
