from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for, session
from functools import wraps
from .models import Event, get_days_in_month, is_leap_year, get_month_name, get_day_of_week, get_weekday_name
from .models import CUSTOM_EPOCH_YEAR, CUSTOM_EPOCH_MONTH, CUSTOM_EPOCH_DAY
from .models import STANDARD_EPOCH_YEAR, STANDARD_EPOCH_MONTH, STANDARD_EPOCH_DAY
from .models import custom_to_standard_date, format_standard_date
from . import db
import os
import json
from datetime import datetime, timedelta

views = Blueprint('views', __name__)

SITE_PASSWORD = os.environ.get('SITE_PASSWORD', 'kalandar')

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('views.login'))
        return f(*args, **kwargs)
    return decorated

@views.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('authenticated'):
        return redirect(url_for('views.calendar'))
    if request.method == 'POST':
        if request.form.get('password') == SITE_PASSWORD:
            session['authenticated'] = True
            return redirect(url_for('views.calendar'))
        flash('Wrong password', category='error')
    return render_template('login.html')

@views.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect(url_for('views.login'))

@views.route('/')
def home():
    return redirect(url_for('views.calendar'))

@views.route('/calendar')
@login_required
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
@login_required
def create_event():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category_select = request.form.get('category', '').strip()
        if category_select == '__custom__':
            category = request.form.get('custom_category', '').strip() or None
        else:
            category = category_select or None

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
                    category=category,
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
        event=None,
        custom_year=custom_year,
        custom_month=custom_month,
        custom_day=custom_day,
        is_leap_year=is_custom_year_leap,
        category_select_value='',
        custom_category_value=''
    )

@views.route('/event/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category_select = request.form.get('category', '').strip()
        if category_select == '__custom__':
            category = request.form.get('custom_category', '').strip() or None
        else:
            category = category_select or None

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
                event.title = title
                event.description = description
                event.category = category
                event.start_time = convert_custom_to_standard_date(year, month, day)
                event.end_time = convert_custom_to_standard_date(year, month, day, 23, 59)
                db.session.commit()
                flash('Event updated!', category='success')
                return redirect(url_for('views.calendar'))
            except ValueError as e:
                flash(f'Invalid date format: {str(e)}', category='error')

    custom_date = convert_standard_to_custom_date(event.start_time)
    is_custom_year_leap = is_leap_year(custom_date['year'])

    # Determine if category is a preset or custom
    preset_categories = ['Die Helden', 'Die Krieger', 'Nerolandes', 'Duos']
    event_category = event.category or ''
    if event_category and event_category not in preset_categories:
        category_select_value = '__custom__'
        custom_category_value = event_category
    else:
        category_select_value = event_category
        custom_category_value = ''

    return render_template(
        "create_event.html",
        event=event,
        custom_year=custom_date['year'],
        custom_month=custom_date['month'],
        custom_day=custom_date['day'],
        is_leap_year=is_custom_year_leap,
        category_select_value=category_select_value,
        custom_category_value=custom_category_value
    )

@views.route('/delete-event', methods=['POST'])
@login_required
def delete_event():
    event_data = json.loads(request.data)
    event_id = event_data['eventId']
    event = Event.query.get(event_id)
    if event:
        db.session.delete(event)
        db.session.commit()
    return jsonify({})

@views.route('/get-events')
@login_required
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
            'category': event.category or '',
            'start': event.start_time.strftime('%Y-%m-%dT%H:%M'),
            'end': event.end_time.strftime('%Y-%m-%dT%H:%M'),
            'customStart': custom_start,
            'customEnd': custom_end,
            'allDay': event.all_day
        })
    return jsonify(event_list)

@views.route('/events')
@login_required
def event_list():
    events = Event.query.order_by(Event.start_time).all()

    # Group events by custom calendar year and month
    # Structure: { year: { month_index: { 'month_name': str, 'events': [...] } } }
    grouped = {}
    for event in events:
        custom_date = convert_standard_to_custom_date(event.start_time)
        year = custom_date['year']
        month = custom_date['month']
        if year not in grouped:
            grouped[year] = {}
        if month not in grouped[year]:
            grouped[year][month] = {
                'month_name': custom_date['month_name'],
                'events': []
            }
        grouped[year][month]['events'].append({
            'id': event.id,
            'title': event.title,
            'description': event.description or '',
            'category': event.category or '',
            'day': custom_date['day'],
            'month_name': custom_date['month_name'],
        })

    # Sort years descending, months ascending within each year
    sorted_years = sorted(grouped.keys(), reverse=True)
    for year in sorted_years:
        grouped[year] = dict(sorted(grouped[year].items()))

    return render_template("events.html",
                           grouped=grouped,
                           sorted_years=sorted_years)

@views.route('/get-date-mappings/<int:year>')
@login_required
def get_date_mappings(year):
    """Get date mappings for a specific custom year"""
    date_mappings = {}
    for month in range(5):
        date_mappings[month] = {}
        for day in range(1, get_days_in_month(month, year) + 1):
            standard_date = custom_to_standard_date(year, month, day)
            date_mappings[month][day] = format_standard_date(standard_date)

    return jsonify(date_mappings)
