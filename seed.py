from datetime import date, time
from app import app, db
from models import User, Event, EventParticipant

with app.app_context():
    # ensure tables exist
    db.create_all()

    # ensure a sample current user exists (this is the user who will join events)
    current = User.query.filter_by(name='Auntie Sue').first()
    if not current:
        current = User(name='Auntie Sue', role='Member')
        db.session.add(current)
        db.session.commit()

    # ensure a host user exists for sample events
    host = User.query.filter_by(name='Host Joe').first()
    if not host:
        host = User(name='Host Joe', role='Host')
        db.session.add(host)
        db.session.commit()

    # sample events (hosted by Host Joe) — only create if not present
    samples = [
        {
            'title': 'Sample Cooking Circle',
            'description': 'Casual cooking for beginners.',
            'date': date(2026, 1, 9),
            'time': time(18, 0),
            'category': 'Cooking',
            'location': 'Community Kitchen',
            'slots': 12,
            'host': host.name,
            'image': None
        },
        {
            'title': 'Sample Tech Meetup',
            'description': 'Intro to Raspberry Pi projects.',
            'date': date(2026, 2, 13),
            'time': time(19, 0),
            'category': 'Technology',
            'location': 'Library Room B',
            'slots': 20,
            'host': host.name,
            'image': None
        }
    ]

    created = []
    for s in samples:
        ev = Event.query.filter_by(title=s['title'], date=s['date']).first()
        if not ev:
            ev = Event(
                title=s['title'],
                description=s['description'],
                date=s['date'],
                time=s['time'],
                category=s['category'],
                location=s['location'],
                slots=s['slots'],
                host=s['host'],
                image=s['image']
            )
            db.session.add(ev)
            db.session.commit()
            created.append(ev)
        else:
            created.append(ev)

    # ensure the current user is NOT already a participant for these sample events
    # (so they appear in Browse allowing the current user to Join)
    for ev in created:
        part = EventParticipant.query.filter_by(user_id=current.id, event_id=ev.id).first()
        if part:
            # if you prefer the sample events to be joinable, remove the existing participant
            # uncomment next two lines to remove:
            # db.session.delete(part)
            # db.session.commit()
            pass

    print("Seed complete. Sample events available:")
    for ev in Event.query.order_by(Event.date, Event.time).all():
        joined = EventParticipant.query.filter_by(event_id=ev.id).count()
        print(f"[{ev.id}] {ev.title} — {ev.date} {ev.time} | host: {ev.host} | joined: {joined}")