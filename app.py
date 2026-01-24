from flask import Flask, render_template, redirect, url_for, request, flash, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models import db, Event, User, EventParticipant, Reflection
from forms import EventForm, ReflectionForm, CreatorReflectionForm
import calendar
from datetime import datetime
import os
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bridgegen.db'
app.config['SECRET_KEY'] = 'change-this'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

# Simulated current user (replace with real auth/session)
def current_user():
    return User.query.first()

# make current_user available in all templates
@app.context_processor
def inject_user():
    return dict(current_user=current_user())

@app.route('/')
def home():
    return redirect(url_for('browse_events'))

# Browse events (R)
@app.route('/events')
def browse_events():
    q = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    query = Event.query
    if q:
        query = query.filter(Event.title.ilike(f'%{q}%'))
    if category:
        query = query.filter(Event.category == category)
    events = query.order_by(Event.date.asc(), Event.time.asc()).all()
    user = current_user()
    joined_ids = {p.event_id for p in EventParticipant.query.filter_by(user_id=user.id).all()} if user else set()
    return render_template('Events/browse.html', events=events, joined_ids=joined_ids, q=q, category=category)

# Event details (R)
@app.route('/events/<int:event_id>')
def event_details(event_id):
    event = Event.query.get_or_404(event_id)
    user = current_user()
    joined = False
    if user:
        joined = EventParticipant.query.filter_by(user_id=user.id, event_id=event.id).first() is not None
    return render_template('Events/details.html', event=event, joined=joined)

# Create event (C)
@app.route('/events/create', methods=['GET', 'POST'])
def create_event():
    form = EventForm()
    user = current_user()
    if not user:
        flash('Please log in to create events.', 'warning')
        return redirect(url_for('browse_events'))

    if form.validate_on_submit():
        # save image if provided
        filename = None
        if form.image.data:
            uploads_dir = os.path.join(app.static_folder, 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            orig = secure_filename(form.image.data.filename)
            ext = os.path.splitext(orig)[1]
            filename = f"{uuid.uuid4().hex}{ext}"
            form.image.data.save(os.path.join(uploads_dir, filename))

        event = Event(
            title=form.title.data,
            description=form.description.data,
            date=form.date.data,
            time=form.time.data,
            category=form.category.data,
            location=form.location.data,
            slots=form.slots.data,
            host=user.name,
            image=filename
        )
        db.session.add(event)
        db.session.commit()

        # automatically add creator as participant (join the event)
        existing = EventParticipant.query.filter_by(user_id=user.id, event_id=event.id).first()
        if not existing:
            participant = EventParticipant(user_id=user.id, event_id=event.id)
            db.session.add(participant)
            db.session.commit()

        flash('Event created and you have been added as a participant.', 'success')
        return redirect(url_for('event_details', event_id=event.id))
    return render_template('Events/create.html', form=form)

# Edit event (U)
@app.route('/events/<int:event_id>/edit', methods=['GET', 'POST'])
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    user = current_user()
    if not user or event.host != user.name:
        flash('Only the event creator can edit this event.', 'warning')
        return redirect(url_for('browse_events'))

    form = EventForm(obj=event)
    # Clear file field initial value if any (WTForms FileField doesn't keep filename)
    # form.image field stays empty

    if form.validate_on_submit():
        # handle image upload (re-upload)
        if form.image.data:
            uploads_dir = os.path.join(app.static_folder, 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            orig = secure_filename(getattr(form.image.data, 'filename', ''))
            if orig:
                ext = os.path.splitext(orig)[1]
                filename = f"{uuid.uuid4().hex}{ext}"
                form.image.data.save(os.path.join(uploads_dir, filename))
                # remove old image if it exists and is not the default
                try:
                    if event.image and event.image != 'default.png':
                        old_path = os.path.join(uploads_dir, event.image)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                except Exception:
                    pass
                event.image = filename

        # update other fields
        event.title = form.title.data
        event.description = form.description.data
        event.date = form.date.data
        event.time = form.time.data
        event.category = form.category.data
        event.location = form.location.data
        event.slots = form.slots.data

        db.session.commit()
        flash('Event updated.', 'success')
        return redirect(url_for('event_details', event_id=event.id))

    return render_template('Events/edit.html', form=form, event=event)

# Delete event (D)
@app.route('/events/<int:event_id>/delete', methods=['POST'])
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted.', 'info')
    return redirect(url_for('browse_events'))

# Join event
@app.route('/events/<int:event_id>/join', methods=['POST'])
def join_event(event_id):
    user = current_user()
    if not user:
        flash('Please log in to join events.', 'warning')
        return redirect(url_for('browse_events'))

    event = Event.query.get_or_404(event_id)
    existing = EventParticipant.query.filter_by(user_id=user.id, event_id=event.id).first()
    if not existing:
        db.session.add(EventParticipant(user_id=user.id, event_id=event.id))
        db.session.commit()
        flash('You joined the event.', 'success')

    # redirect back to the page that made the request (details or browse).
    dest = request.referrer or url_for('browse_events')
    return redirect(dest)

# Leave event
@app.route('/events/<int:event_id>/leave', methods=['POST'])
def leave_event(event_id):
    user = current_user()
    if not user:
        flash('Please log in to leave events.', 'warning')
        return redirect(url_for('browse_events'))

    part = EventParticipant.query.filter_by(user_id=user.id, event_id=event_id).first()
    if part:
        db.session.delete(part)
        db.session.commit()
        flash('You left the event.', 'info')

    dest = request.referrer or url_for('browse_events')
    return redirect(dest)

# My events (calendar + joined/created + reflection)
@app.route('/my-events')
def my_events():
    user = current_user()
    if not user:
        flash('Please log in to view your events.', 'warning')
        return redirect(url_for('browse_events'))

    # all joined events (including those the user created — needed for calendar/highlights)
    joined_all = (db.session.query(Event)
                  .join(EventParticipant, Event.id == EventParticipant.event_id)
                  .filter(EventParticipant.user_id == user.id)
                  .order_by(Event.date.asc(), Event.time.asc())
                  .all())

    # joined_for_list: exclude events where the user is the host so they appear only under "Created"
    joined = [e for e in joined_all if e.host != user.name]

    # created events
    created = Event.query.filter(Event.host == user.name).order_by(Event.date.asc()).all()

    # month/year selection via query params (defaults to current month/year)
    try:
        sel_month = int(request.args.get('month', datetime.utcnow().month))
        sel_year = int(request.args.get('year', datetime.utcnow().year))
    except ValueError:
        sel_month = datetime.utcnow().month
        sel_year = datetime.utcnow().year

    # days and layout info for the selected month
    num_days = calendar.monthrange(sel_year, sel_month)[1]
    first_weekday = calendar.monthrange(sel_year, sel_month)[0]  # 0 = Monday
    leading_blanks = first_weekday

    # use joined_all for calendar/highlight computation so creator-attended events still highlight
    joined_in_month = [e for e in joined_all if e.date.month == sel_month and e.date.year == sel_year]
    joined_days = {e.date.day for e in joined_in_month}

    # reflections (attended) for joined events in selected month -> green
    joined_event_ids = [e.id for e in joined_in_month]
    attended_days = set()
    if joined_event_ids:
        attended = Reflection.query.filter(Reflection.user_id == user.id, Reflection.event_id.in_(joined_event_ids)).all()
        attended_event_ids = {r.event_id for r in attended}
        events_map = {e.id: e for e in joined_in_month}
        for eid in attended_event_ids:
            ev = events_map.get(eid)
            if ev:
                attended_days.add(ev.date.day)

    # prev/next month links
    if sel_month == 1:
        prev_month, prev_year = 12, sel_year - 1
    else:
        prev_month, prev_year = sel_month - 1, sel_year
    if sel_month == 12:
        next_month, next_year = 1, sel_year + 1
    else:
        next_month, next_year = sel_month + 1, sel_year

    month_name = calendar.month_name[sel_month]

    return render_template('Events/my_events.html',
                           joined=joined,               # shown in "Events Joined" (creator excluded)
                           created=created,
                           sel_month=sel_month,
                           sel_year=sel_year,
                           month_name=month_name,
                           num_days=num_days,
                           leading_blanks=leading_blanks,
                           joined_days=joined_days,     # calendar highlights (includes creator events)
                           attended_days=attended_days,
                           prev_month=prev_month,
                           prev_year=prev_year,
                           next_month=next_month,
                           next_year=next_year)

# Reflection (C)
@app.route('/reflection/<int:event_id>', methods=['GET', 'POST'])
def reflection(event_id):
    event = Event.query.get_or_404(event_id)
    user = current_user()
    if not user:
        flash('Please log in to submit a reflection.', 'warning')
        return redirect(url_for('browse_events'))

    # allow reflection if user joined OR is the event host
    participant = EventParticipant.query.filter_by(user_id=user.id, event_id=event.id).first()
    if not participant and event.host != user.name:
        flash('Only participants or the event creator can submit reflections.', 'warning')
        return redirect(url_for('browse_events'))

    form = ReflectionForm()
    existing = Reflection.query.filter_by(user_id=user.id, event_id=event.id).first()

    # populate form when editing existing reflection
    if request.method == 'GET' and existing:
        try:
            form.rating.data = existing.rating
            form.comments.data = existing.comments
        except Exception:
            pass

    if form.validate_on_submit():
        if existing:
            existing.rating = form.rating.data
            existing.comments = form.comments.data
            existing.submitted_at = datetime.utcnow()  # update timestamp
        else:
            new_ref = Reflection(
                user_id=user.id,
                event_id=event.id,
                rating=form.rating.data,
                comments=form.comments.data,
                submitted_at=datetime.utcnow()  # ensure non-null timestamp
            )
            db.session.add(new_ref)
        db.session.commit()
        flash('Reflection submitted.', 'success')
        return redirect(url_for('my_events'))

    return render_template('reflection.html', form=form, event=event)

# Creator Reflection (C)
@app.route('/reflection/creator/<int:event_id>', methods=['GET', 'POST'])
def creator_reflection(event_id):
    event = Event.query.get_or_404(event_id)
    user = current_user()
    if not user:
        flash('Please log in to submit a creator reflection.', 'warning')
        return redirect(url_for('browse_events'))

    # only allow the event host to use this creator reflection form
    if event.host != user.name:
        flash('Only the event creator can submit a creator reflection here.', 'warning')
        return redirect(url_for('browse_events'))

    form = CreatorReflectionForm()
    existing = Reflection.query.filter_by(user_id=user.id, event_id=event.id).first()

    # populate form when editing existing reflection
    if request.method == 'GET' and existing:
        form.rating.data = existing.rating
        form.comments.data = existing.comments

    if form.validate_on_submit():
        if existing:
            existing.rating = form.rating.data
            existing.comments = form.comments.data
            existing.submitted_at = datetime.utcnow()  # update timestamp
            db.session.commit()
            flash('You have updated your post reflection.', 'success')
        else:
            new_ref = Reflection(
                user_id=user.id,
                event_id=event.id,
                rating=form.rating.data,
                comments=form.comments.data,
                submitted_at=datetime.utcnow()  # set required timestamp
            )
            db.session.add(new_ref)
            db.session.commit()
            flash('You have submitted your post reflection.', 'success')
        return redirect(url_for('my_events'))

    return render_template('reflection_creator.html', form=form, event=event)

if __name__ == '__main__':
    with app.app_context():
        # create a seed user if none exists
        if User.query.count() == 0:
            db.session.add(User(name='Auntie Sue', role='Senior'))
            db.session.commit()
    app.run(debug=True, port=5001)