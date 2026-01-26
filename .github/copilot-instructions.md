# BridgeGen AI Copilot Instructions

## Project Overview
BridgeGen is an intergenerational social platform (Flask + SQLAlchemy) connecting users through events, stories, communities, and real-time messaging. Target: seniors and intergenerational communities.

**Tech Stack:**
- Backend: Flask 3.1.2, SQLAlchemy 2.0.45, Flask-SocketIO 5.6.0, Flask-Login
- Database: SQLite (`bridgegen_complete.db`) with association tables for relationships
- Frontend: Jinja2 templates, JavaScript, SocketIO for real-time features
- Deployment: Gunicorn + eventlet (0.40.4) single worker for WebSocket stability
- Static serving: `css/` folder for stylesheets, `css/js/` for client code, `css/uploads/` for user files

## Architecture & Core Concepts

### Entity Relationships (models.py)
**User** (hub model):
- `friends`: bidirectional many-to-many via `connections` association table
- `hobbies`, `interests`: many-to-many for profile matching
- `stories`, `sent_messages`, `received_messages`: one-to-many backrefs
- Password: stored as `_password_hash` (werkzeug); use `set_password()/check_password()` methods
- `background_color`: theme customization field

**Content Models**:
- **Story** (narrative): `privacy` (Public/Friends/Private), `media` (comma-sep filenames), `voice_recording`, `tags`, `timestamp`, `likes`, `saved`
- **Event** (time-bound): `host` (username string), `slots` (int), `category` (predefined enum), `EventParticipant` registrations, `Reflection` ratings
- **Community** (group): `CommunityMember` with roles (admin/member), `Post` (with `PostLike`/`CommunityComment`)
- **Message** (one-on-one): defined in [chat_routes.py](chat_routes.py); `sender_id`/`receiver_id` for bidirectional queries, `is_read` flag, `sender`/`receiver` relationships with backrefs

**Key Pattern**: Association tables (`connections`, `user_hobbies`, `user_interests`) enable efficient many-to-many queries and friend discovery.

### Critical Data Flows
1. **Authentication**: LoginForm → `User.check_password()` validates → Flask-Login session → `current_user` available in routes/templates
2. **Real-time Chat**: 
   - Join: User connects → auto-joins `user_{user_id}` room; `active_users[user_id] = socket_id` tracked
   - Send: `@socketio.on('send_message')` creates `Message` record → `emit('receive_message', message.to_dict(), room=f'user_{receiver_id}')`
   - Receive: client JS `socket.on('receive_message')` updates DOM; marks `is_read=True` when opened
   - Persistence: All messages stored in `Message` table with `sender_id`/`receiver_id`; chat history queried from DB, not from active memory
3. **Events**: EventForm submission → Event + EventParticipant rows → User submits Reflection → aggregated stats
4. **Community**: User joins as CommunityMember → creates Posts → receives Comments/Likes

## Developer Workflows & Commands

### Local Setup & Running
```bash
# Install dependencies
pip install -r requirements.txt

# Development: Run with debug + auto-reload
python -c "from app import app, socketio; socketio.run(app, debug=True, port=5000)"

# Or use Flask CLI:
export FLASK_APP=app.py
export FLASK_ENV=development
flask run
```

### Database Operations
- **Create tables**: Call `db.create_all()` in app context (already seeded in `seed_data()`)
- **Query patterns**: Always use `User.query.filter_by(username='x').first()` or `db.session.query()` syntax
- **Commit**: Explicit `db.session.commit()` required after `add()`/`delete()`
- **Transactions**: Wrap multi-step operations in try/except with `db.session.rollback()` on error

### Adding Features
1. **Model**: Define class in [models.py](models.py), create relationships with backrefs
2. **Form**: Create WTForm in [forms.py](forms.py) with validators (see `EventForm`, `StoryForm` examples)
3. **Route**: Add `@app.route()` in [app.py](app.py), use `@login_required` for protected endpoints
4. **Template**: Create Jinja2 file in `html/`, extend `base.html`, include `{{ csrf_token() }}` in forms
5. **Database**: Ensure `db.session.add()` → `db.session.commit()` in route handler

### Testing Real-Time Features Locally
- Open browser console to inspect SocketIO messages
- Check `active_users` dict in app for online status
- Inspect `Message` table directly: `sqlite3 bridgegen_complete.db "SELECT * FROM message;"`

## Code Patterns & Conventions

### Password Handling
```python
# ALWAYS use these methods in User model:
user.set_password(password_string)  # Hashes and stores
user.check_password(password_string)  # Verifies
# Do NOT store plaintext; the `_password_hash` column is the actual storage
```

### Login & Session Flow
```python
# Protected routes MUST use @login_required
# Current user always available via: current_user (Flask-Login injection)
# Legacy support: get_current_user() also works
```

### SocketIO Room-Based Messaging
- Users join `user_{user_id}` room on connect
- Messages emitted to `room=f'user_{receiver_id}'` for recipient
- `active_users` dict tracks {user_id: socket_id} for online status

### File Upload Pattern (from forms.py, app.py)
```python
# In form: FileField('Image', validators=[Optional(), FileAllowed(['jpg','png','gif'])])
# In route:
if file and file.filename:
    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    # Store filename (not full path) in database
```

### Form Validation
- All user input validated via WTForms validators in [forms.py](forms.py)
- EventForm, StoryForm use FileField with FileAllowed() restrictions
- Custom tags and reflections have max length constraints

### ✓ DO
- Use `current_user` from Flask-Login (injected automatically) instead of `session['user_id']`
- Hash passwords with `user.set_password(plaintext)` before storing; verify with `check_password()`
- Validate forms before DB operations: `if form.validate_on_submit()`
- Use `@property` for computed values (e.g., `Community.member_count` queries CommunityMember table)
- Emit SocketIO events to specific room: `emit('event_name', data, room=f'user_{id}')`
- Commit explicitly: `db.session.commit()` not auto-flush
- Query with `.filter()` for conditions: `User.query.filter(User.id != current_user.id).all()`

### ✗ DON'T
- Store plaintext passwords; always use `_password_hash` column
- Hardcode user IDs in routes—reference `current_user.id` from Flask-Login
- Assume users are online without checking `active_users` dict first
- Create circular imports (e.g., `app.py` → `models.py` → `app.py`)
- Use `@app.route` for SocketIO handlers; use `@socketio.on('event_name')` instead
- Broadcast messages to all users; always emit to specific `room=`
- Modify Event.host as user ID—it's stored as username string (design quirk; refactor if extending)
- Skip `@login_required` on routes accessing user data

## Project Structure Reference
```
BridgeGen/
├── app.py              # Flask app, route handlers, SocketIO setup (~2100 lines)
├── chat_routes.py      # Message model + chat endpoints (partially integrated into app.py—sync before extending)
├── models.py           # 12 SQLAlchemy models (User, Event, Story, Community, Message, etc.)
├── forms.py            # WTForms validators for all user inputs
├── html/               # 30+ Jinja2 templates
│   ├── base.html       # Layout wrapper (CSS includes, theme support)
│   ├── auth.html       # Login/register forms
│   ├── event_*.html    # Event CRUD, browsing, details, reflections
│   ├── story_*.html    # Story creation, viewing, editing, commenting
│   ├── community_*.html # Community features (browsing, creation, posts)
│   ├── chat.html       # Real-time messaging UI
│   ├── profile.html    # User settings, profile customization
│   └── footer.html, notifications.html
├── css/
│   ├── style.css       # Main stylesheet
│   ├── js/
│   │   ├── chat.js     # SocketIO client, message handling, typing indicator
│   │   ├── login.js    # Form validation
│   │   └── story_script.js # Story interactions
│   ├── colourcustomiser/ # Theme manager (thememanager.js updates background_color)
│   └── uploads/        # User-generated images (chicken_rice.avif example)
├── requirements.txt    # 45+ dependencies (Flask, SQLAlchemy, eventlet, etc.)
└── Procfile           # Deployment: gunicorn --worker-class eventlet -w 1 app:app
```

**⚠️ Chat Integration Note**: The `Message` model is defined in [chat_routes.py](chat_routes.py) but SocketIO handlers may also be in `app.py`. When extending chat features, check both files for duplicate definitions before adding new endpoints.

## Key Dependencies & Version Notes
- **Flask 3.1.2**, **SQLAlchemy 2.0.45**: Modern async-capable ORM; supports dynamic relationships
- **Flask-SocketIO 5.6.0** + **python-socketio 5.16.0**: WebSocket with fallback; namespace support
- **eventlet 0.40.4**: WSGI worker for concurrency (Procfile requires `-w 1` for stability)
- **WTForms 3.2.1**: Server-side validation with CSRF protection
- **finnhub-python 2.4.23**: Included but unused in core features (likely for future expansion)

## Troubleshooting & Common Issues

| Issue | Solution |
|-------|----------|
| User not authenticated in route | Add `@login_required` decorator; verify `current_user.is_authenticated` is True |
| Real-time message not delivering | Check receiver in `active_users` dict; verify room name format `f'user_{receiver_id}'` |
| Form validation fails silently | Inspect `form.errors` dict in Jinja2 debug; check validators in `forms.py` |
| Database changes not persisting | Ensure explicit `db.session.commit()` after `add()` |
| WebSocket disconnects on production | Verify Procfile: `gunicorn --worker-class eventlet -w 1` (single worker required) |
| Static files not loading | Check `css/` path in Flask init: `template_folder='html', static_folder='css'` |
| File uploads 400/413 error | Verify `UPLOAD_FOLDER` exists, `secure_filename()` used, file size under limit |

## AI Agent Constraints & Scope
- **Modify**: Routes, models, forms, templates, static assets
- **Test locally first**: Always run with `socketio.run(app, debug=True)` before production suggestions
- **Preserve**: User session flow, password hashing, SocketIO room structure, single eventlet worker
- **Avoid**: Changing `bridgegen_complete.db` URI, adding complex dependencies, altering database schema without migration
- **Document**: When adding models/routes, update this file with data flow and usage examples

## Session & Authentication Details
- LoginManager configured to redirect unauthenticated users to `auth` route
- `session['user_id']` set by Flask-Login after successful authentication
- Legacy `get_current_user()` function available but prefer `current_user` from Flask-Login
- Friends (and similar relationships) queryable via SQLAlchemy dynamic relationship
- Theme customization persisted in `User.background_color` (updated by theme manager JS)
