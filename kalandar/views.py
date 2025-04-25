from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from .models import Event, get_days_in_month, is_leap_year, get_month_name, get_day_of_week, get_weekday_name
from .models import CUSTOM_EPOCH_YEAR, CUSTOM_EPOCH_MONTH, CUSTOM_EPOCH_DAY
from .models import STANDARD_EPOCH_YEAR, STANDARD_EPOCH_MONTH, STANDARD_EPOCH_DAY
from .models import custom_to_standard_date, format_standard_date
from . import db
import json
from datetime import datetime, timedelta

views = Blueprint('views', __name__)

@views.route('/')
def home():
    return redirect(url_for('views.calendar'))

@views.route('/calendar')
def calendar():
    # Get today's date in the custom calendar
    today = datetime.now()
    custom_today = convert_standard_to_custom_date(today)
    
    # Debug output
    print(f"Calendar view: Today's custom date is {custom_today['year']}-{custom_today['month']}-{custom_today['day']}")
    
    # Create date mapping for the JavaScript part
    date_mappings = {}
    for month in range(5):
        date_mappings[month] = {}
        for day in range(1, get_days_in_month(month, custom_today['year']) + 1):
            # Convert custom date to standard date
            standard_date = custom_to_standard_date(custom_today['year'], month, day)
            # Format the standard date
            date_mappings[month][day] = format_standard_date(standard_date)
    
    return render_template("calendar.html", 
                          custom_today=custom_today,
                          date_mappings=date_mappings)

def convert_standard_to_custom_date(standard_date):
    """Convert a standard calendar date to our custom 5-month calendar date"""
    from .models import standard_to_custom_date
    
    # Get the custom date using the model function
    custom_date = standard_to_custom_date(standard_date)
    
    # Add time information
    custom_date['hour'] = standard_date.hour
    custom_date['minute'] = standard_date.minute
    
    print(f"Converting {standard_date} to custom date: {custom_date}")
    
    return custom_date

def convert_custom_to_standard_date(year, month, day, hour=0, minute=0):
    """Convert our custom 5-month calendar date to a standard date"""
    from .models import custom_to_standard_date
    
    # Get the standard date using the model function
    standard_date = custom_to_standard_date(year, month, day)
    
    # Add time information
    if hour != 0 or minute != 0:
        standard_date = standard_date.replace(hour=hour, minute=minute)
    
    return standard_date

@views.route('/event', methods=['GET', 'POST'])
def create_event():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        
        # Get custom calendar inputs
        year = int(request.form.get('year', datetime.now().year))
        month = int(request.form.get('month', 0))
        day = int(request.form.get('day', 1))
        
        if not title:
            flash('Event must have a title', category='error')
        else:
            try:
                # Convert custom dates to standard dates
                start_time = convert_custom_to_standard_date(year, month, day)
                # Set end time to the end of the day since all events are all-day
                end_time = convert_custom_to_standard_date(year, month, day, 23, 59)
                
                # Check if the Event model has the all_day attribute
                if hasattr(Event, 'all_day'):
                    new_event = Event(
                        title=title,
                        description=description,
                        start_time=start_time,
                        end_time=end_time,
                        all_day=True
                    )
                else:
                    new_event = Event(
                        title=title,
                        description=description,
                        start_time=start_time,
                        end_time=end_time
                    )
                db.session.add(new_event)
                db.session.commit()
                flash('Event added!', category='success')
                return redirect(url_for('views.calendar'))
            except ValueError as e:
                flash(f'Invalid date format: {str(e)}', category='error')
                
    # For GET requests, render with date data from parameters or current date
    # Check if date parameters were passed in request
    year = request.args.get('year')
    month = request.args.get('month')
    day = request.args.get('day')
    
    if year and month and day:
        # Use provided date parameters
        custom_year = int(year)
        custom_month = int(month)
        custom_day = int(day)
    else:
        # Use current date
        current_date = datetime.now()
        custom_date = convert_standard_to_custom_date(current_date)
        custom_year = custom_date['year']
        custom_month = custom_date['month']
        custom_day = custom_date['day']
    
    is_custom_year_leap = is_leap_year(custom_year)
    
    return render_template(
        "create_event.html", 
        custom_year=custom_year,
        custom_month=custom_month,
        custom_day=custom_day,
        is_leap_year=is_custom_year_leap
    )

@views.route('/delete-event', methods=['POST'])
def delete_event():
    event_data = json.loads(request.data)
    event_id = event_data['eventId']
    event = Event.query.get(event_id)
    if event:
        db.session.delete(event)
        db.session.commit()
    return jsonify({})

@views.route('/get-events')
def get_events():
    events = Event.query.all()
    event_list = []
    for event in events:
        # Convert to custom calendar format for frontend
        custom_start = convert_standard_to_custom_date(event.start_time)
        custom_end = convert_standard_to_custom_date(event.end_time)
        
        print(f"Converting event: ID={event.id}, Start={event.start_time}, custom_start={custom_start}")
        event_list.append({
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'start': event.start_time.strftime('%Y-%m-%dT%H:%M'),
            'end': event.end_time.strftime('%Y-%m-%dT%H:%M'),
            'customStart': custom_start,
            'customEnd': custom_end,
            'allDay': event.all_day if hasattr(event, 'all_day') else True
        })
    return jsonify(event_list)

@views.route('/get-date-mappings/<int:year>')
def get_date_mappings(year):
    """Get date mappings for a specific custom year"""
    # Debug output
    print(f"Generating date mappings for year: {year}")
    
    # Create date mapping for the given year
    date_mappings = {}
    for month in range(5):
        date_mappings[month] = {}
        for day in range(1, get_days_in_month(month, year) + 1):
            # Convert custom date to standard date
            standard_date = custom_to_standard_date(year, month, day)
            # Format the standard date
            date_mappings[month][day] = format_standard_date(standard_date)
    
    # Log the first few mappings to verify
    print(f"Sample mappings for year {year}: Month 0, Day 1 = {date_mappings[0][1]}")
    
    return jsonify(date_mappings)