from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from .models import Event, get_days_in_month, is_leap_year, get_month_name
from . import db
import json
from datetime import datetime, timedelta

views = Blueprint('views', __name__)

@views.route('/')
def home():
    return redirect(url_for('views.calendar'))

@views.route('/calendar')
def calendar():
    return render_template("calendar.html")

def convert_standard_to_custom_date(standard_date):
    """Convert a standard calendar date to our custom 5-month calendar date"""
    # Get day of year (1-366)
    day_of_year = standard_date.timetuple().tm_yday
    
    # Convert to our custom calendar system
    month = 0
    day = day_of_year
    
    # Find the month
    while month < 4 and day > get_days_in_month(month, standard_date.year):
        day -= get_days_in_month(month, standard_date.year)
        month += 1
    
    # Check if we're in a valid date range
    if month == 4 and day > get_days_in_month(4, standard_date.year):
        # Date is out of range for our calendar
        month = 4
        day = get_days_in_month(4, standard_date.year)
    
    return {
        'year': standard_date.year,
        'month': month,  # 0-based
        'month_name': get_month_name(month),
        'day': day,
        'hour': standard_date.hour,
        'minute': standard_date.minute
    }

def convert_custom_to_standard_date(year, month, day, hour=0, minute=0):
    """Convert our custom 5-month calendar date to a standard date"""
    # Calculate day of year
    day_of_year = day
    for m in range(month):
        day_of_year += get_days_in_month(m, year)
    
    # Convert to standard date
    start_of_year = datetime(year, 1, 1)
    standard_date = start_of_year + timedelta(days=day_of_year-1, hours=hour, minutes=minute)
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
        start_hour = int(request.form.get('start_hour', 0))
        start_minute = int(request.form.get('start_minute', 0))
        end_hour = int(request.form.get('end_hour', 1))
        end_minute = int(request.form.get('end_minute', 0))
        
        if not title:
            flash('Event must have a title', category='error')
        else:
            try:
                # Convert custom dates to standard dates
                start_time = convert_custom_to_standard_date(year, month, day, start_hour, start_minute)
                end_time = convert_custom_to_standard_date(year, month, day, end_hour, end_minute)
                
                if start_time >= end_time:
                    flash('End time must be after start time', category='error')
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
                
    # For GET requests, render with current year data
    current_year = datetime.now().year
    is_current_year_leap = is_leap_year(current_year)
    
    return render_template(
        "create_event.html", 
        current_year=current_year,
        is_leap_year=is_current_year_leap
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
        
        event_list.append({
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'start': event.start_time.strftime('%Y-%m-%dT%H:%M'),
            'end': event.end_time.strftime('%Y-%m-%dT%H:%M'),
            'customStart': custom_start,
            'customEnd': custom_end
        })
    return jsonify(event_list)