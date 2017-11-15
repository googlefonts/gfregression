"""
Script deletes all dirs in static/fonts_after and static/fonts_before.

Hook this up to a cron and execute every week, month etc; depending on
server capacity/performance.
"""
import fontmanager

fontmanager.remove_font_dirs()
print 'Removed fonts!'
