"""Setup rethinkdb for diffenator"""
import rethinkdb as r

__all__ = ['build_tables']


def build_tables():
    connection = r.connect("localhost", 28015).repl()


    try:
        r.db_create("diffenator_web").run()
    except r.errors.ReqlOpFailedError:
        print 'Skipping db creation, it already exists'


    for table in ('fonts', 'fontsets', 'comparisons', 'glyphs'):
        try:
            r.db("diffenator_web").table_create(table).run()
            print 'Created %s table' % table
        except r.errors.ReqlOpFailedError:
            print 'Skipping %s table creation, they already exist' % table

    connection.close()
