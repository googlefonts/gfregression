import os
import re
import shutil
import requests
import json
try:
    from StringIO import StringIO
except ModuleNotFoundError:  # py3 workaround
    from io import BytesIO as StringIO

# Info taken from https://caniuse.com/#feat=variable-fonts
MIN_VF_BROWSERS = {
    'chrome': 67,
    'firefox': 62,
    'edge': 17,
    'safari': 11,
}

GF_FAMILY_IGNORE_CAMEL = {
    'ABeeZee': 'ABeeZee',
    'AlegreyaSC': 'Alegreya SC',
    'AlegreyaSansSC': 'Alegreya Sans SC',
    'AlmendraSC': 'Almendra SC',
    'AmaticSC': 'Amatic SC',
    'AmaticaSC': 'Amatica SC',
    'BowlbyOneSC': 'Bowlby One SC',
    'CarroisGothicSC': 'Carrois Gothic SC',
    'CormorantSC': 'Cormorant SC',
    'DiplomataSC': 'Diplomata SC',
    'EBGaramond': 'EB Garamond',
    'GFSDidot': 'GFS Didot',
    'GFSNeohellenic': 'GFS Neohellenic',
    'HoltwoodOneSC': 'Holtwood One SC',
    'IMFellDWPica': 'IM Fell DW Pica',
    'IMFellDWPicaSC': 'IM Fell DW Pica SC',
    'IMFellDoublePica': 'IM Fell Double Pica',
    'IMFellDoublePicaSC': 'IM Fell Double Pica SC',
    'IMFellEnglish': 'IM Fell English',
    'IMFellEnglishSC': 'IM Fell English SC',
    'IMFellFrenchCanon': 'IM Fell French Canon',
    'IMFellFrenchCanonSC': 'IM Fell French Canon SC',
    'IMFellGreatPrimer': 'IM Fell Great Primer',
    'IMFellGreatPrimerSC': 'IM Fell Great Primer SC',
    'MarcellusSC': 'Marcellus SC',
    'MateSC': 'Mate SC',
    'NTR': 'NTR',
    'OldStandardTT': 'Old Standard TT',
    'OverlockSC': 'Overlock SC',
    'PTMono': 'PT Mono',
    'PTSans': 'PT Sans',
    'PTSansCaption': 'PT Sans Caption',
    'PTSansNarrow': 'PT Sans Narrow',
    'PTSerif': 'PT Serif',
    'PTSerifCaption': 'PT Serif Caption',
    'PatrickHandSC': 'Patrick Hand SC',
    'PlayfairDisplaySC': 'Playfair Display SC',
    'VollkornSC': 'Vollkorn SC',
    'VT323': 'VT323',
    'B612': 'B612',
    'B612Mono': 'B612 Mono',
}

GF_STYLE_TERMS = {
    'Thin': 'Thin',
    'ExtraLight': 'Extralight',
    'Light': 'Light',
    'Regular': 'Regular',
    'Medium': 'Medium',
    'SemiBold': 'SemiBold',
    'Bold': 'Bold',
    'ExtraBold': 'ExtraBold',
    'Black': 'Black',
    'ThinItalic': 'Thin Italic',
    'ExtraLightItalic': 'ExtraLight Italic',
    'LightItalic': 'Light Italic',
    'Italic': 'Italic',
    'MediumItalic': 'MediumItalic',
    'SemiBoldItalic': 'SemiBold Italic',
    'BoldItalic': 'Bold Italic',
    'ExtraBoldItalic': 'ExtraBold Italic',
    'BlackItalic': 'Black Italic',
}


def browser_supports_vfs(user_agent):
    """Check if the user's browser supports variable fonts

    Parameters
    ----------
    user_agent: werkzeug.useragents.UserAgent

    Returns
    -------
    Boolean"""
    user_browser = user_agent.browser
    browser_version = int(user_agent.version.split('.')[0])
    if user_browser not in MIN_VF_BROWSERS:
        return False
    if browser_version < MIN_VF_BROWSERS[user_browser]:
        return False
    return True


def download_file(url, dst_path=None):
    """Download a file from a url. If no url is specified, store the file
    as a StringIO object"""
    request = requests.get(url, stream=True)
    if not dst_path:
        return StringIO(request.content)
    with open(dst_path, 'wb') as downloaded_file:
        shutil.copyfileobj(request.raw, downloaded_file)


def family_name_from_filename(filename, seperator=' '):
    """RubikMonoOne-Regular > Rubik Mono One"""
    family = filename.split('-')[0]
    if family not in list(GF_FAMILY_IGNORE_CAMEL.keys()):
        return re.sub('(?!^)([A-Z]|[0-9]+)', r'%s\1' % seperator, family)
    else:
        return GF_FAMILY_IGNORE_CAMEL[family]


def style_name_from_filename(filename, seperator=' '):
    """RubikMonoOne-Regular --> Regular"""
    try:
        style = filename.split('-')[1]
        return GF_STYLE_TERMS[style]
    except:
        return 'Regular'


with open("secrets.json") as f:
    secrets = json.loads(f.read())

def secret(key, secret=secrets):
    try:
        return secret[key]
    except KeyError:
        raise Exception('Secret {} does not exist'.format(secret))
