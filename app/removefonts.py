"""
Script deletes all fonts in static/fonts and comparison data.

Hook this up to a cron and execute every week, month etc; depending on
server capacity/performance.
"""
import os
import rethinkdb as r

from settings import FONTS_DIR

connection = r.connect("localhost", 28015, 'diffenator_web').repl()

for table in ('fonts', 'fontsets', 'comparisons', 'glyphs'):
    print 'Deleting %s' % table
    r.table(table).delete().run()
connection.close()

print('Deleting static/fonts/*.ttf')
for f in os.listdir(FONTS_DIR):
    if f.endswith('.ttf'):
        font_path = os.path.join(FONTS_DIR, f)
        os.remove(font_path)
