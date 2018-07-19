import models
from glob import glob 
import shutil
import os

fonts_before_src = '/Users/marc/Downloads/mini'
fonts_after_src = '/Users/marc/Documents/googlefonts/manual_font_cleaning/_privates/Roboto/test'

# fonts_after_src = fonts_before_src


fonts_before = './f_before'
fonts_after = './f_after'

shutil.rmtree(fonts_before)
shutil.rmtree(fonts_after)

shutil.copytree(fonts_before_src, fonts_before)
shutil.copytree(fonts_after_src, fonts_after)

fonts_before = glob(fonts_before + '/*.ttf')
fonts_after = glob(fonts_after + '/*.ttf')

fonts_before = models.add_fonts(fonts_before, 'before', '1234')
fonts_after = models.add_fonts(fonts_after, 'after', '1234')


styles_before = models.add_styles(fonts_before)
styles_after = models.add_styles(fonts_after)
styles_before, styles_after = models.match_styles(styles_before, styles_after)

fontset = models.add_fontset(fonts_before, styles_before, fonts_after, styles_after, '1234')


diffs = models.add_font_diffs(styles_before, styles_after, '1234')


print diffs