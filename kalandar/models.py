from . import db
from sqlalchemy.sql import func
import calendar

# Configure custom calendar with 5 months
# First 4 months with 90 days, 5th month with 5 days (6 in leap year)
def is_leap_year(year):
    return calendar.isleap(year)

def get_days_in_month(month, year):
    if month < 5:  # First 4 months
        return 90
    else:  # 5th month
        return 6 if is_leap_year(year) else 5

def get_total_days_in_year(year):
    return 366 if is_leap_year(year) else 365

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.String(1000))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())