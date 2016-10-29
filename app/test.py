import unittest
from main import fonts_on_google


class GoogleFontsApi(unittest.TestCase):
    def test_get_google_fontface_url_from_local_font(self):
        """Test we can convert a local font's path into a compatible url for
        the Google fonts api"""
        inconsolata_reg_url = 'https://fonts.googleapis.com/css?family=Inconsolata:400'
        inconsolata_local = [('path/Inconsolata-Regular.ttf', 'Inconsolata-Regular')]

        self.assertEqual(fonts_on_google(inconsolata_local),
                         [('Inconsolata',
                           'Inconsolata',
                           '400',
                           'normal',
                           inconsolata_reg_url)])


if __name__ == '__main__':
    unittest.main()
