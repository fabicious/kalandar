from . import db
from sqlalchemy.sql import func
import calendar
from datetime import datetime, timedelta

# Configure custom calendar with 5 months and 10-day weeks
# First 4 months (Astira, Grin, Train, Windugi) with 90 days each
# Last month (Kus) with 5 days (6 in leap year)
# 
# Epoch reference: January 1, 1970 (UNIX epoch) = 11th of Astira 1520

# The custom calendar epoch is defined as:
CUSTOM_EPOCH_YEAR = 1520  # Custom calendar year corresponding to 1970
CUSTOM_EPOCH_MONTH = 0    # Astira (0-indexed)
CUSTOM_EPOCH_DAY = 11     # 11th day of Astira

# Standard epoch for reference
STANDARD_EPOCH_YEAR = 1970
STANDARD_EPOCH_MONTH = 1  # January
STANDARD_EPOCH_DAY = 1

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

def standard_to_days_since_epoch(year, month, day):
    """Convert a standard date to days since the standard epoch (Jan 1, 1970)"""
    date = datetime(year, month, day)
    epoch = datetime(STANDARD_EPOCH_YEAR, STANDARD_EPOCH_MONTH, STANDARD_EPOCH_DAY)
    return (date - epoch).days

def _day_of_year(year, month, day):
    """1-based day-of-year for a custom calendar date."""
    doy = day
    for m in range(month):
        doy += get_days_in_month(m, year)
    return doy

def custom_to_days_since_epoch(year, month, day):
    """Convert a custom calendar date to days since the custom epoch (11 Astira 1520).
    Returns negative values for dates before the epoch."""
    target_doy = _day_of_year(year, month, day)
    epoch_doy = _day_of_year(CUSTOM_EPOCH_YEAR, CUSTOM_EPOCH_MONTH, CUSTOM_EPOCH_DAY)

    if year == CUSTOM_EPOCH_YEAR:
        return target_doy - epoch_doy
    elif year > CUSTOM_EPOCH_YEAR:
        # Days remaining in epoch year + full intermediate years + target doy
        days = get_total_days_in_year(CUSTOM_EPOCH_YEAR) - epoch_doy
        for y in range(CUSTOM_EPOCH_YEAR + 1, year):
            days += get_total_days_in_year(y)
        days += target_doy
        return days
    else:
        # year < epoch: go backward
        days = epoch_doy
        for y in range(year + 1, CUSTOM_EPOCH_YEAR):
            days += get_total_days_in_year(y)
        days += get_total_days_in_year(year) - target_doy
        return -days

def custom_to_standard_date(custom_year, custom_month, custom_day):
    """Convert a custom calendar date to a standard Gregorian date"""
    # Get days since epoch for the custom date
    days_since_custom_epoch = custom_to_days_since_epoch(custom_year, custom_month, custom_day)
    
    # Create a standard date by adding the days to the standard epoch
    standard_epoch = datetime(STANDARD_EPOCH_YEAR, STANDARD_EPOCH_MONTH, STANDARD_EPOCH_DAY)
    standard_date = standard_epoch + timedelta(days=days_since_custom_epoch)
    
    return standard_date

def format_standard_date(date):
    """Format a standard date in a short format (MM/DD/YY)"""
    return date.strftime("%m/%d/%y")

def standard_to_custom_date(standard_date):
    """Convert a standard Gregorian date to our custom calendar date"""
    days_since_standard_epoch = standard_to_days_since_epoch(
        standard_date.year, standard_date.month, standard_date.day)

    # Start at epoch: Astira 11, 1520.  Compute doy then shift by offset.
    year = CUSTOM_EPOCH_YEAR
    epoch_doy = _day_of_year(CUSTOM_EPOCH_YEAR, CUSTOM_EPOCH_MONTH, CUSTOM_EPOCH_DAY)
    doy = epoch_doy + days_since_standard_epoch

    # Normalize year forward
    while doy > get_total_days_in_year(year):
        doy -= get_total_days_in_year(year)
        year += 1

    # Normalize year backward
    while doy < 1:
        year -= 1
        doy += get_total_days_in_year(year)

    # Decompose doy into month/day
    month = 0
    for m in range(5):
        dim = get_days_in_month(m, year)
        if doy <= dim:
            month = m
            break
        doy -= dim
    day = doy

    return {
        'year': year,
        'month': month,
        'month_name': get_month_name(month),
        'day': day,
        'weekday': get_day_of_week(custom_day_of_year(year, month, day)),
        'weekday_name': get_weekday_name(get_day_of_week(custom_day_of_year(year, month, day)))
    }

def custom_day_of_year(year, month, day):
    """Calculate the day of year in the custom calendar"""
    day_of_year = day
    for m in range(month):
        day_of_year += get_days_in_month(m, year)
    return day_of_year

def get_day_of_week(day_of_year):
    """Returns the day of week (1-10) for a given day of year in our custom calendar"""
    return ((day_of_year - 1) % 10) + 1

def get_weekday_name(day_of_week):
    """Returns the name of the weekday (1-10)"""
    weekday_names = ['Antag', 'Zwitag', 'Tretag', 'Vietig', 'Fürtag', 
                     'Sechsa', 'Septag', 'Achtag', 'Nune', 'Entag']
    if 1 <= day_of_week <= 10:
        return weekday_names[day_of_week - 1]
    return None

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
    category = db.Column(db.String(100), nullable=True)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    all_day = db.Column(db.Boolean, default=True)
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())