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
    today = datetime.now()
    custom_today = convert_standard_to_custom_date(today)

    date_mappings = {}
    for month in range(5):
        date_mappings[month] = {}
        for day in range(1, get_days_in_month(month, custom_today['year']) + 1):
            standard_date = custom_to_standard_date(custom_today['year'], month, day)
            date_mappings[month][day] = format_standard_date(standard_date)

    return render_template("calendar.html",
                           custom_today=custom_today,
                           date_mappings=date_mappings)

def convert_standard_to_custom_date(standard_date):
    """Convert a standard calendar date to our custom 5-month calendar date"""
    from .models import standard_to_custom_date

    custom_date = standard_to_custom_date(standard_date)
    custom_date['hour'] = standard_date.hour
    custom_date['minute'] = standard_date.minute

    return custom_date

def convert_custom_to_standard_date(year, month, day, hour=0, minute=0):
    """Convert our custom 5-month calendar date to a standard date"""
    from .models import custom_to_standard_date

    standard_date = custom_to_standard_date(year, month, day)

    if hour != 0 or minute != 0:
        standard_date = standard_date.replace(hour=hour, minute=minute)

    return standard_date

@views.route('/event', methods=['GET', 'POST'])
def create_event():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')

        year = int(request.form.get('year', datetime.now().year))
        month = int(request.form.get('month', 0))
        day = int(request.form.get('day', 1))

        if not title:
            flash('Event must have a title', category='error')
        elif year <= 0:
            flash('Invalid year', category='error')
        elif not (0 <= month <= 4):
            flash('Invalid month', category='error')
        elif not (1 <= day <= get_days_in_month(month, year)):
            flash('Invalid day for the selected month', category='error')
        else:
            try:
                start_time = convert_custom_to_standard_date(year, month, day)
                end_time = convert_custom_to_standard_date(year, month, day, 23, 59)

                new_event = Event(
                    title=title,
                    description=description,
                    start_time=start_time,
                    end_time=end_time,
                    all_day=True
                )
                db.session.add(new_event)
                db.session.commit()
                flash('Event added!', category='success')
                return redirect(url_for('views.calendar'))
            except ValueError as e:
                flash(f'Invalid date format: {str(e)}', category='error')

    year = request.args.get('year')
    month = request.args.get('month')
    day = request.args.get('day')

    if year and month and day:
        custom_year = int(year)
        custom_month = int(month)
        custom_day = int(day)
    else:
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
        custom_start = convert_standard_to_custom_date(event.start_time)
        custom_end = convert_standard_to_custom_date(event.end_time)

        custom_start['day'] = str(custom_start['day'])
        custom_start['month'] = str(custom_start['month'])
        custom_start['year'] = str(custom_start['year'])

        custom_end['day'] = str(custom_end['day'])
        custom_end['month'] = str(custom_end['month'])
        custom_end['year'] = str(custom_end['year'])

        event_list.append({
            'id': event.id,
            'title': event.title,
            'description': event.description if event.description else '',
            'start': event.start_time.strftime('%Y-%m-%dT%H:%M'),
            'end': event.end_time.strftime('%Y-%m-%dT%H:%M'),
            'customStart': custom_start,
            'customEnd': custom_end,
            'allDay': event.all_day
        })
    return jsonify(event_list)

@views.route('/get-date-mappings/<int:year>')
def get_date_mappings(year):
    """Get date mappings for a specific custom year"""
    date_mappings = {}
    for month in range(5):
        date_mappings[month] = {}
        for day in range(1, get_days_in_month(month, year) + 1):
            standard_date = custom_to_standard_date(year, month, day)
            date_mappings[month][day] = format_standard_date(standard_date)

    return jsonify(date_mappings)
