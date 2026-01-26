from flask import Flask, render_template, redirect, url_for, flash, session, request
from models import db, User, Event, Story, ChatMessage, Notification
from forms import RegistrationForm, LoginForm, EventForm, StoryForm, ChatForm

# Set template_folder to 'html' as requested
app = Flask(__name__, template_folder='html')
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bridgegen.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Create Database Tables
with app.app_context():
    db.create_all()

# --- Helpers ---
def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

# --- Routes ---

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    # Handle both Login and Register on one page (Split Screen Logic)
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'register':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            
            if User.query.filter_by(email=email).first():
                flash('Email exists!', 'danger')
            else:
                new_user = User(username=username, email=email)
                new_user.password = password
                db.session.add(new_user)
                db.session.commit()
                flash('Account created! Please login.', 'success')

        elif action == 'login':
            email = request.form.get('email')
            password = request.form.get('password')
            user = User.query.filter_by(email=email).first()
            if user and user.verify_password(password):
                session['user_id'] = user.id
                return redirect(url_for('profile'))
            else:
                flash('Login Failed', 'danger')
                
    return render_template('auth.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

@app.route('/events', methods=['GET', 'POST'])
def events():
    user = get_current_user()
    form = EventForm()
    if form.validate_on_submit() and user:
        new_event = Event(title=form.title.data, location=form.location.data, 
                          event_date=form.date.data, author=user)
        db.session.add(new_event)
        
        # Create Notification
        notif = Notification(message=f"New Event created: {new_event.title}", user_id=user.id)
        db.session.add(notif)
        
        db.session.commit()
        return redirect(url_for('events'))
        
    events = Event.query.all()
    return render_template('events.html', events=events, form=form, user=user)

@app.route('/story', methods=['GET', 'POST'])
def story():
    user = get_current_user()
    form = StoryForm()
    if form.validate_on_submit() and user:
        new_story = Story(title=form.title.data, content=form.content.data, author=user)
        db.session.add(new_story)
        db.session.commit()
        return redirect(url_for('story'))
        
    stories = Story.query.all()
    return render_template('story.html', stories=stories, form=form, user=user)

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    user = get_current_user()
    form = ChatForm()
    if form.validate_on_submit() and user:
        msg = ChatMessage(username=user.username, message=form.message.data)
        db.session.add(msg)
        db.session.commit()
        return redirect(url_for('chat'))
        
    messages = ChatMessage.query.order_by(ChatMessage.timestamp.desc()).limit(20).all()
    return render_template('chat.html', messages=messages, form=form, user=user)

@app.route('/community')
def community():
    users = User.query.all()
    return render_template('community.html', users=users)

@app.route('/notifications')
def notifications():
    user = get_current_user()
    if not user: return redirect(url_for('auth'))
    
    notifs = Notification.query.filter_by(user_id=user.id).order_by(Notification.timestamp.desc()).all()
    return render_template('notifications.html', notifications=notifs)

@app.route('/profile')
def profile():
    user = get_current_user()
    if not user: return redirect(url_for('auth'))
    return render_template('profile.html', user=user)

if __name__ == '__main__':
    app.run(debug=True)