from peewee import *
import datetime


db = SqliteDatabase('fuzz.db')

class BaseModel(Model):
    class Meta:
        database = db

class Target(BaseModel):
    next_sequence = IntegerField(default=0)
    messages = IntegerField()
    depth = IntegerField()
    running = BooleanField(default=False)
    started_at = DateTimeField(default=datetime.datetime.now)
    completed_at = DateTimeField(default=datetime.datetime.now)
    processed = IntegerField(default=0)

    @property
    def last_sequence(self):
        return int(str(self.messages - 1) * self.depth, self.messages)

class Crash(BaseModel):
    target = ForeignKeyField(Target, backref='crashes')
    signal = CharField()
    reason = CharField()
    sequence = IntegerField()
    instruction = IntegerField()
    offset = IntegerField()
    path = CharField()
    log = TextField()
    reported_at = DateTimeField(default=datetime.datetime.now)

class Packet(BaseModel):
    crash = ForeignKeyField(Crash, backref='packets')
    index = SmallIntegerField()
    data = BlobField()


if __name__ == '__main__':
    db.create_tables([Target, Crash, Packet])
    Target(messages=4, depth=3).save()
