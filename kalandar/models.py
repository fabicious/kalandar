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

def custom_to_days_since_epoch(year, month, day):
    """Convert a custom calendar date to days since the custom epoch (11 Astira 1520)"""
    # Calculate days between years
    days = 0
    
    # Add days for complete years before the target year
    for y in range(CUSTOM_EPOCH_YEAR, year):
        days += get_total_days_in_year(y)
    
    # Add days within the target year up to the target month
    for m in range(CUSTOM_EPOCH_MONTH, month):
        days += get_days_in_month(m, year)
    
    # Add days within the target month up to the target day
    days += day - CUSTOM_EPOCH_DAY
    
    return days

def custom_to_standard_date(custom_year, custom_month, custom_day):
    """Convert a custom calendar date to a standard Gregorian date"""
    # Get days since epoch for the custom date
    days_since_custom_epoch = custom_to_days_since_epoch(custom_year, custom_month, custom_day)
    
    # Create a standard date by adding the days to the standard epoch
    standard_epoch = datetime(STANDARD_EPOCH_YEAR, STANDARD_EPOCH_MONTH, STANDARD_EPOCH_DAY)
    standard_date = standard_epoch + timedelta(days=days_since_custom_epoch)
    
    return standard_date

def standard_to_custom_date(standard_date):
    """Convert a standard Gregorian date to our custom calendar date"""
    # Calculate days since standard epoch
    days_since_standard_epoch = standard_to_days_since_epoch(
        standard_date.year, standard_date.month, standard_date.day)
    
    # Start from the custom epoch
    custom_year = CUSTOM_EPOCH_YEAR
    custom_month = CUSTOM_EPOCH_MONTH
    custom_day = CUSTOM_EPOCH_DAY
    
    # Add the days to the custom date
    remaining_days = days_since_standard_epoch
    
    # Advance years
    while True:
        days_in_year = get_total_days_in_year(custom_year)
        if remaining_days >= days_in_year:
            remaining_days -= days_in_year
            custom_year += 1
        else:
            break
    
    # Advance months
    while True:
        days_in_month = get_days_in_month(custom_month, custom_year)
        if remaining_days >= days_in_month:
            remaining_days -= days_in_month
            custom_month += 1
            if custom_month >= 5:  # Wrap to next year
                custom_month = 0
                custom_year += 1
        else:
            break
    
    # Advance days
    custom_day += remaining_days
    
    # Check if we need to advance to next month
    days_in_current_month = get_days_in_month(custom_month, custom_year)
    if custom_day > days_in_current_month:
        custom_day -= days_in_current_month
        custom_month += 1
        if custom_month >= 5:  # Wrap to next year
            custom_month = 0
            custom_year += 1
    
    return {
        'year': custom_year,
        'month': custom_month,
        'month_name': get_month_name(custom_month),
        'day': custom_day,
        'weekday': get_day_of_week(custom_day_of_year(custom_year, custom_month, custom_day)),
        'weekday_name': get_weekday_name(get_day_of_week(custom_day_of_year(custom_year, custom_month, custom_day)))
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
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())