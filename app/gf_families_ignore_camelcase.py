from utils import secret
import requests
import re
import json
import os


def gf_families_ignore_camelcase():
    """Find family names in the GF collection which cannot be derived by
    splitting the filename using a camelcase function e.g

    VT323, PTSans.
    
    If these filenames are split, they will be V T 323 and P T Sans."""
    families = {}
    api_url = 'https://www.googleapis.com/webfonts/v1/webfonts?key={}'.format(
        secret('GF_API_KEY')
    )
    r = requests.get(api_url)
    for item in r.json()["items"]:
        if re.search(r"[A-Z]{2}", item['family']):
            families[item["family"].replace(" ", "")] = item["family"]
    return families


def main():
    current_dir = os.path.dirname(__file__)
    families = gf_families_ignore_camelcase()
    out = os.path.join(current_dir, "gf_families_ignore_camelcase.json")
    json.dump(families , open(out, 'w'))


if __name__ == "__main__":
    main()
