from . import db
from sqlalchemy.sql import func
import calendar

# Configure custom calendar with 5 months and 10-day weeks
# First 4 months (Astira, Grin, Train, Windugi) with 90 days each
# Last month (Kus) with 5 days (6 in leap year)
def is_leap_year(year):
    return calendar.isleap(year)

def get_month_name(month):
    """Returns the name of the month (0-indexed)"""
    month_names = ['Astira', 'Grin', 'Train', 'Windugi', 'Kus']
    if 0 <= month < len(month_names):
        return month_names[month]
    return None

def get_days_in_month(month, year):
    if month < 4:  # First 4 months (Astira, Grin, Train, Windugi)
        return 90
    elif month == 4:  # 5th month (Kus)
        return 6 if is_leap_year(year) else 5
    else:
        return 0  # Invalid month

def get_total_days_in_year(year):
    return 366 if is_leap_year(year) else 365

def get_day_of_week(day_of_year):
    """Returns the day of week (1-10) for a given day of year in our custom calendar"""
    return ((day_of_year - 1) % 10) + 1

def get_week_of_month(day, month, year):
    """Returns the week number within the month"""
    day_of_year = 0
    # Add days from previous months
    for m in range(month):
        day_of_year += get_days_in_month(m, year)
    # Add days from current month
    day_of_year += day
    
    # Calculate week number (1-indexed)
    return ((day - 1) // 10) + 1

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.String(1000))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())