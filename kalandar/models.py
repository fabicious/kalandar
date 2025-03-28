from . import db
from sqlalchemy.sql import func

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.String(1000))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())