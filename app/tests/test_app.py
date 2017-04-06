import unittest
from app.main import (
    _convert_camelcase,
    URL_PREFIX,
    url_200_response,
)


class GoogleFontsApi(unittest.TestCase):

    def test_api_url_still_works(self):
        """Check the download api url is still operational"""
        real_family_dl_url = url_200_response('%sInconsolata' % URL_PREFIX)
        fake_family_dl_url = url_200_response('%sThisIsAFauxFont' % URL_PREFIX)
        self.assertEqual(real_family_dl_url, True)
        self.assertEqual(fake_family_dl_url, False)

    def test_convert_camelcase(self):
        sngl_name = 'Anaheim'
        dbl_name = 'BadScript'
        self.assertEqual(_convert_camelcase(sngl_name, '+'), 'Anaheim')
        self.assertEqual(_convert_camelcase(dbl_name, '+'), 'Bad+Script')
        self.assertEqual(_convert_camelcase(dbl_name), 'Bad Script')


if __name__ == '__main__':
    unittest.main()
