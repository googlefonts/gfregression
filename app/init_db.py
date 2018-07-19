"""Setup rethinkdb for diffenator"""
import rethinkdb as r

__all__ = ['build_tables']


def build_tables(host, port, db):
    connection = r.connect(host=host, port=port, db=db).repl()
    try:
        r.db_create(db).run()
    except r.errors.ReqlOpFailedError:
        print 'Skipping db creation, it already exists'

    for table in ('families', 'families_diffs'):
        try:
            r.db(db).table_create(table).run()
            print 'Created %s table' % table
        except r.errors.ReqlOpFailedError:
            print 'Skipping %s table creation, they already exist' % table

    connection.close()
