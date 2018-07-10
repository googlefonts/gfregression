from diffenator import diff_fonts


def compare_fonts(fonts_before, fonts_after, uuid):
    comparisons = {'uuid': uuid}
    shared_fonts = set([f['full_name'] for f in fonts_before]) & \
                   set([f['full_name'] for f in fonts_after])
    fonts_before = {f['full_name']: f for f in fonts_before}
    fonts_after = {f['full_name']: f for f in fonts_after}

    for font in shared_fonts:
        font_before_path = fonts_before[font]['filename']
        font_after_path = fonts_after[font]['filename']

        comparison = diff_fonts(font_before_path, font_after_path)

        for cat in comparison:
            if cat not in ('glyphs', 'kern', 'metrics', 'marks', 'mkmks'):
                continue
            for subcat in comparison[cat]:
                key = '{}_{}'.format(cat, subcat)
                if not key in comparisons:
                    title = '{} {}'.format(cat.title(), subcat.title())
                    comparisons[key] = {'title': title, 'tests': []}
                comparisons[key]['tests'].append({
                        'font_before': fonts_before[font],
                        'font_after': fonts_after[font],
                        'glyphs': comparison[cat][subcat]
                })
    _comparisons_serialiser(comparisons)
    return comparisons


def _comparisons_serialiser(d):
    """Serialise diffenator's diff object"""
    for k in d:
        if isinstance(d[k], dict):
            _comparisons_serialiser(d[k])
        elif isinstance(d[k], list):
            for idx, item in enumerate(d[k]):
                _comparisons_serialiser(item)
        elif hasattr(d[k], 'kkey'):
            d[k] = dict(d[k].__dict__)
    return d
