import models
from fontTools.ttLib import TTFont


f = TTFont('/Users/marc/Documents/googlefonts/manual_font_cleaning/_privates/Roboto/variable_ttf/Roboto-VF.ttf')

print models._get_vf_styles(f)