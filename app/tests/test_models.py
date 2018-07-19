from app import models

import unittest


class TestMain(unittest.TestCase):
    def test_get_css_weight_from_style(self):
        self.assertEqual(_get_css_weight_from_style('BlackItalic'), 900)

if __name__ == '__main__':
    unittest.main()
