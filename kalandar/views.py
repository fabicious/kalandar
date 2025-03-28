from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from .models import Event
from . import db
import json
from datetime import datetime

views = Blueprint('views', __name__)

@views.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('views.calendar'))
    return render_template("home.html", user=current_user)

@views.route('/calendar')
@login_required
def calendar():
    return render_template("calendar.html", user=current_user)

@views.route('/event', methods=['GET', 'POST'])
@login_required
def create_event():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')
        
        if not title:
            flash('Event must have a title', category='error')
        elif not start_time_str or not end_time_str:
            flash('Event must have start and end times', category='error')
        else:
            try:
                start_time = datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M')
                end_time = datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M')
                
                if start_time >= end_time:
                    flash('End time must be after start time', category='error')
                else:
                    new_event = Event(
                        title=title,
                        description=description,
                        start_time=start_time,
                        end_time=end_time,
                        user_id=current_user.id
                    )
                    db.session.add(new_event)
                    db.session.commit()
                    flash('Event added!', category='success')
                    return redirect(url_for('views.calendar'))
            except ValueError:
                flash('Invalid date format', category='error')
                
    return render_template("create_event.html", user=current_user)

@views.route('/delete-event', methods=['POST'])
def delete_event():
    event_data = json.loads(request.data)
    event_id = event_data['eventId']
    event = Event.query.get(event_id)
    if event:
        if event.user_id == current_user.id:
            db.session.delete(event)
            db.session.commit()
    return jsonify({})

@views.route('/get-events')
@login_required
def get_events():
    events = Event.query.filter_by(user_id=current_user.id).all()
    event_list = []
    for event in events:
        event_list.append({
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'start': event.start_time.strftime('%Y-%m-%dT%H:%M'),
            'end': event.end_time.strftime('%Y-%m-%dT%H:%M')
        })
    return jsonify(event_list)
