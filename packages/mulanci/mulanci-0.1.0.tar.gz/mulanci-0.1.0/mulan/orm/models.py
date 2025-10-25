from peewee import Model, TextField, IntegerField, ForeignKeyField
from playhouse.shortcuts import model_to_dict
from playhouse.sqlite_ext import JSONField, SqliteExtDatabase

database = SqliteExtDatabase(
    None,
    pragmas={
        'journal_mode': 'wal',
        'cache_size': 50000,
        'foreign_keys': 0,
    },
    autoconnect=False,
)

class BaseModel(Model):
    id = TextField(primary_key=True)

    class Meta:
        database = database
