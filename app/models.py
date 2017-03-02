from peewee import (
    SqliteDatabase,
    Model,
    CharField,
    IntegerField,
    TextField,
    )


db = SqliteDatabase('iso639corpora.db')


class Languages(Model):
    name = CharField()
    part1 = CharField(null=True)
    part2 = CharField(null=True)
    part3 = CharField(null=True)
    wiki_id = IntegerField(null=True)
    text = TextField(null=True)

    class Meta:
        database = db # This model uses the "people.db" database.
