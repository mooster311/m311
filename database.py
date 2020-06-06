from peewee import *
import datetime
from playhouse.pool import PooledMySQLDatabase
from dotenv import load_dotenv
import os
load_dotenv()

db = PooledMySQLDatabase(os.getenv("DB"), user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"), host=os.getenv("DB_HOST"), max_connections=32,
                         stale_timeout=300)


class Service(Model):
    name = CharField()
    port = IntegerField()
    mods = TextField()
    service = CharField()

    class Meta:
        database = db


class Logging(Model):
    online = BooleanField()
    service = ForeignKeyField(Service, backref='logs')
    created_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db


class Ping(Model):
    ping = FloatField()
    service = ForeignKeyField(Service, backref='pings')
    created_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db


class HourlyData(Model):
    ping = FloatField()
    uptime = FloatField()
    service = ForeignKeyField(Service, lazy_load=False)
    created_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db


class DailyData(Model):
    ping = FloatField()
    uptime = FloatField()
    service = ForeignKeyField(Service, lazy_load=False)
    created_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db


if __name__ == '__main__':
    db.drop_tables([Logging, Service, Ping, HourlyData, DailyData])
    db.create_tables([Service, Logging, Ping, HourlyData, DailyData])
