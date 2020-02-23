import mongoengine
import datetime


class Snake(mongoengine.Document):
    registered_date = mongoengine.DateTimeField(default=datetime.datetime.now)
    species = mongoengine.StringField(required=True)

    length =  mongoengine.FloatField(required=True)
    name = mongoengine.StringField()
    is_venomous = mongoengine.BooleanField()

    meta = {
        'db_alias': 'core',
        'collections': 'snakes'
    }
