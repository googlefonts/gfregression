from peewee import *


db = SqliteDatabase('iso639corpora.db')


class Languages(Model):
    name = CharField()
    part1 = CharField(null=True)
    part2 = CharField(null=True)
    part3 = CharField(null=True)
    text = TextField(null=True)

    class Meta:
        database = db # This model uses the "people.db" database.
