#!/usr/bin/env python3
"""Update .github/copilot-instructions.md with streamlined AI agent guidance."""

content = """# BridgeGen AI Copilot Instructions

## Project Overview
**BridgeGen** is an intergenerational social platform (Flask + SQLAlchemy) enabling seniors and cross-generational users to connect through events, stories, communities, and real-time messaging.

**Stack**: Flask 3.1.2, Flask-Login, Flask-SocketIO, SQLite, Jinja2, eventlet (single-worker WSGI)

---

## Core Data Model

### Central Entity: User
```python
# Password: Always use user.set_password(pwd) / check_password(pwd) (NOT plaintext)
# Friends: Bidirectional via 'connections' association table
# Profile: includes background_color for theme customization
```

### Content Entities
- **Story**: Privacy-controlled narratives (Public/Friends/Private) with media, voice, tags
- **Event**: Time-bound activities → EventParticipant → Reflection (1-5 ratings)
- **Community**: Groups with CommunityMember (roles: member/admin), Posts, Comments
- **Message**: One-on-one chat (sender_id + receiver_id for bilateral queries)

### Association Tables
- `connections` (bidirectional friendships)
- `user_hobbies`, `user_interests` (profile matching)

---

## Critical Patterns

### 1. Authentication & Session
```python
@login_required  # Protect sensitive routes
current_user     # Flask-Login injected current user (preferred over session['user_id'])
user.set_password(pwd)  # Hash with werkzeug
```

### 2. Real-Time Chat (SocketIO)
```python
@socketio.on('send_message')
# 1. Save Message to DB (sender_id, receiver_id, timestamp)
# 2. Emit to room: emit('receive_message', ..., room=f'user_{receiver_id}')
# 3. Track online status in active_users dict
```

### 3. File Uploads
- Store in `css/uploads/` (see app.py config)
- Use `secure_filename()` on upload
- Whitelist: jpg, jpeg, png, gif (images); mp4, mov, avi (videos)

### 4. Form Validation
- All input via WTForms in forms.py
- Example: `FileField(..., FileAllowed(['jpg', 'png'], 'Images only'))`
- Validate **before** `db.session.commit()`

### 5. Database Queries
```python
# Filter with relationships:
user.friends.filter_by(username=x).first()
# Bidirectional message search:
Message.query.filter(db.or_(
    db.and_(Message.sender_id == a, Message.receiver_id == b),
    db.and_(Message.sender_id == b, Message.receiver_id == a)
)).all()
```

---

## Project Structure

```
BridgeGen/
├── app.py              # Routes, SocketIO, LoginManager (1793 lines)
├── models.py           # 15 models: User, Event, Story, Community, Message, etc.
├── forms.py            # 7 WTForms: Registration, Event, Story, Reflection, Chat
├── chat_routes.py      # Chat endpoints (consider merging into app.py)
├── html/               # 30+ Jinja2 templates (extend base.html)
│   ├── base.html       # Layout, navbar, accessibility tools, footer
│   ├── auth.html       # Login/register
│   ├── chat.html       # SocketIO-driven UI + draggable accessibility tools
│   ├── event_*.html    # CRUD: create, browse, details, edit, reflections
│   ├── story_*.html    # CRUD: create, browse, details, edit, confirm dialogs
│   └── community_*.html # Create, browse, detail, member posts
├── css/
│   ├── style.css       # Main stylesheet
│   ├── colourcustomiser/ # thememanager.js (user background_color)
│   ├── js/             # chat.js, login.js, story_script.js
│   └── uploads/        # User images/media
└── Procfile            # gunicorn --worker-class eventlet -w 1 app:app
```

---

## Developer Workflows

### Adding a Feature
1. **Model**: Add class + relationships to models.py
2. **Form**: WTForm in forms.py for user input
3. **Route**: Add `@app.route()` handler in app.py
4. **Template**: Create/extend Jinja2 in html/
5. **Database**: `db.session.add()` then `db.session.commit()`

### Running Locally
```bash
pip install -r requirements.txt
python -c "from app import app, socketio; socketio.run(app, debug=True, port=5000)"
```

### Key Dependencies
- **Flask-SocketIO 5.6.0**: WebSocket messaging (chat)
- **eventlet 0.40.4**: Single-worker WSGI for concurrency
- **WTForms 3.2.1**: Server-side validation
- **Flask-Login + werkzeug**: Authentication and password hashing

---

## Do's and Don'ts

| Do | Don't |
|------|---------|
| Use current_user from Flask-Login | Store passwords in plaintext |
| Validate forms before DB operations | Hardcode host as string in Event |
| Use @property for computed values | Skip @login_required on sensitive routes |
| Commit transactions explicitly | Assume user is online without checking |
| Query bidirectionally for Message | Run multiple workers with eventlet |

---

## Debugging

| Issue | Solution |
|-------|----------|
| User not authenticated | Add @login_required + verify LoginManager.user_loader |
| Real-time chat not delivering | Check receiver in active_users dict |
| Form silently fails | Inspect form.errors in template |
| Database not persisting | Add explicit db.session.commit() |
| WebSocket disconnect on production | Use single worker: gunicorn --worker-class eventlet -w 1 |

---

## Agent Notes
- **Scope**: Add routes, models, templates, forms
- **Avoid**: Changing DB URI, Procfile, worker concurrency
- **Test**: Always run socketio.run(app, debug=True) locally first
- **Preserve**: User session flow, profile customization, community roles
"""

with open('.github/copilot-instructions.md', 'w') as f:
    f.write(content)
    
print('✓ .github/copilot-instructions.md updated successfully!')
