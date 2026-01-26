from flask import Flask, render_template, redirect, url_for, flash, session, request, jsonify
from models import db, User, Event, Story, StoryComment, ChatMessage, Notification, Hobby, Interest, EventParticipant, Reflection, Community, CommunityMember, Post, CommunityComment, PostLike, CommunityEvent, Message
from forms import RegistrationForm, LoginForm, EventForm, StoryForm, ChatForm, ReflectionForm, CreatorReflectionForm
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
from werkzeug.utils import secure_filename
from flask import send_from_directory 
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
import itertools
from datetime import datetime
import calendar
import uuid


app = Flask(__name__, template_folder='html', static_folder='css')
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bridgegen_complete.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
socketio = SocketIO(app)
active_users = {}

# --- FIXED: INITIALIZE LOGIN MANAGER ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth' # Redirect here if user tries to access protected page

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- HELPER: Get Current User (Legacy Support) ---
# You can now use 'current_user' directly, but keeping this for your existing code
def get_current_user():
    if current_user.is_authenticated:
        return current_user
    return None

# --- DATABASE SEEDER ---
def seed_data():
    hobbies_list = ['Coding', 'Gardening', 'Gaming', 'Cooking', 'Music']
    for h_name in hobbies_list:
        if not Hobby.query.filter_by(name=h_name).first():
            db.session.add(Hobby(name=h_name))
            
    interests_list = ['Family', 'History', 'Food', 'Work Life', 'Travel', 'Health']
    for i_name in interests_list:
        if not Interest.query.filter_by(name=i_name).first():
            db.session.add(Interest(name=i_name))
    
    # Add sample users if they don't exist
    sample_users = ['Yong', 'Lim Wei', 'Chen Hui', 'Margaret', 'Sarah']
    for username in sample_users:
        if not User.query.filter_by(username=username).first():
            user = User(username=username, email=f"{username.lower().replace(' ', '')}@example.com", dob='1990-01-01')
            user.set_password('password123')
            db.session.add(user)
    
    db.session.commit()
    
    # Add sample events if they don't exist
    if Event.query.count() == 0:
        sample_events = [
            Event(
                title='Traditional Dumpling Making Workshop',
                description='Learn the art of making traditional Chinese dumplings from our experienced seniors. Perfect for beginners! We\'ll cover different folding techniques and share family recipes passed down through generations.',
                date=datetime(2026, 2, 5).date(),
                time=datetime.strptime('14:00', '%H:%M').time(),
                category='Cooking',
                location='Community Center, Toa Payoh Block 5',
                slots=15,
                host='Lim Wei',
                image='default.png'
            ),
            Event(
                title='Python for Beginners Workshop',
                description='Join us for a hands-on Python programming workshop! Perfect for seniors who want to learn coding basics. We\'ll cover variables, loops, and build a simple calculator app together.',
                date=datetime(2026, 2, 8).date(),
                time=datetime.strptime('10:00', '%H:%M').time(),
                category='Technology',
                location='Ngee Ann Polytechnic, Block 51',
                slots=20,
                host='Yong',
                image='default.png'
            ),
            Event(
                title='Morning Tai Chi at Botanic Gardens',
                description='Start your day with energizing Tai Chi exercises in the beautiful Singapore Botanic Gardens. Suitable for all fitness levels. Bring your own mat!',
                date=datetime(2026, 2, 1).date(),
                time=datetime.strptime('07:00', '%H:%M').time(),
                category='Fitness',
                location='Singapore Botanic Gardens, Palm Valley',
                slots=25,
                host='Margaret',
                image='default.png'
            ),
            Event(
                title='Vintage Photography Walk',
                description='Explore the historic streets of Chinatown while learning vintage photography techniques. Bring your camera or smartphone. We\'ll share tips on composition, lighting, and capturing Singapore\'s heritage.',
                date=datetime(2026, 2, 10).date(),
                time=datetime.strptime('15:30', '%H:%M').time(),
                category='Art',
                location='Chinatown Heritage Centre',
                slots=12,
                host='Yong',
                image='default.png'
            ),
            Event(
                title='Community Gardening Day',
                description='Help us beautify our neighborhood! Join fellow residents in planting flowers and vegetables in our community garden. Tools and refreshments provided. Great way to meet neighbors!',
                date=datetime(2026, 2, 12).date(),
                time=datetime.strptime('09:00', '%H:%M').time(),
                category='Environmental',
                location='Bishan Community Garden',
                slots=30,
                host='Chen Hui',
                image='default.png'
            ),
            Event(
                title='Guitar Jam Session for Beginners',
                description='Bring your guitar and join us for a casual jam session! Whether you\'re just starting out or have been playing for years, everyone is welcome. We\'ll play classic oldies and modern hits.',
                date=datetime(2026, 2, 15).date(),
                time=datetime.strptime('18:00', '%H:%M').time(),
                category='Music',
                location='Esplanade Outdoor Theatre',
                slots=18,
                host='Sarah',
                image='default.png'
            ),
            Event(
                title='Coffee Chat: Life Stories',
                description='Join us for a relaxed afternoon of coffee and conversation. Share your life experiences, listen to others\' stories, and make new friends across generations. Refreshments provided!',
                date=datetime(2026, 2, 6).date(),
                time=datetime.strptime('15:00', '%H:%M').time(),
                category='Social',
                location='Starbucks, Orchard Central',
                slots=10,
                host='Lim Wei',
                image='default.png'
            ),
            Event(
                title='Heritage Craft Workshop: Batik Painting',
                description='Discover the beautiful art of batik painting! Learn traditional techniques and create your own batik masterpiece to take home. All materials included. No experience necessary.',
                date=datetime(2026, 2, 18).date(),
                time=datetime.strptime('13:00', '%H:%M').time(),
                category='Craft',
                location='Kampong Glam Community Centre',
                slots=15,
                host='Chen Hui',
                image='default.png'
            ),
            Event(
                title='Board Games & Snacks Night',
                description='Dust off those classic board games and join us for a fun evening! From Monopoly to Scrabble, we\'ll have a variety of games. Bring your favorites or try something new. Snacks provided!',
                date=datetime(2026, 2, 20).date(),
                time=datetime.strptime('19:00', '%H:%M').time(),
                category='Social',
                location='Tampines Regional Library',
                slots=20,
                host='Margaret',
                image='default.png'
            ),
            Event(
                title='Coastal Cleanup at East Coast Park',
                description='Make a difference for our environment! Join us in cleaning up East Coast Park beach. Gloves and bags provided. Stay after for a beach picnic and socializing!',
                date=datetime(2026, 2, 22).date(),
                time=datetime.strptime('08:00', '%H:%M').time(),
                category='Environmental',
                location='East Coast Park, Area C',
                slots=40,
                host='Yong',
                image='default.png'
            ),
            Event(
                title='Mandarin Conversation Circle',
                description='Improve your Mandarin Chinese in a relaxed, friendly setting. Native speakers welcome to help out! All levels from beginner to advanced. Hot tea and snacks provided.',
                date=datetime(2026, 2, 24).date(),
                time=datetime.strptime('14:00', '%H:%M').time(),
                category='Social',
                location='Jurong Regional Library',
                slots=15,
                host='Chen Hui',
                image='default.png'
            ),
            Event(
                title='Healthy Cooking: Low-Sodium Recipes',
                description='Learn to prepare delicious meals while keeping sodium intake in check. Perfect for seniors managing blood pressure. Chef will demonstrate and provide recipe cards. Tasting session included!',
                date=datetime(2026, 2, 25).date(),
                time=datetime.strptime('10:00', '%H:%M').time(),
                category='Cooking',
                location='Bukit Merah Community Centre',
                slots=20,
                host='Margaret',
                image='default.png'
            ),
            Event(
                title='Smartphone Basics Workshop',
                description='Master the basics of your smartphone! Learn about apps, taking photos, video calls, and staying safe online. One-on-one support available. Bring your own device.',
                date=datetime(2026, 2, 27).date(),
                time=datetime.strptime('11:00', '%H:%M').time(),
                category='Technology',
                location='Ang Mo Kio Community Club',
                slots=25,
                host='Lim Wei',
                image='default.png'
            ),
            Event(
                title='Walking Tour: Hidden Gems of Singapore',
                description='Discover lesser-known spots and stories of Singapore! Our local expert will guide you through hidden alleys, heritage trails, and scenic viewpoints. Easy pace, suitable for all fitness levels.',
                date=datetime(2026, 3, 1).date(),
                time=datetime.strptime('09:00', '%H:%M').time(),
                category='Outdoor',
                location='Meet at Raffles Hotel, Singapore',
                slots=22,
                host='Sarah',
                image='default.png'
            ),
            Event(
                title='Watercolor Painting Basics',
                description='Express your creativity with watercolor! Learn basic techniques including washes, glazing, and wet-on-wet methods. All materials provided. No prior experience needed.',
                date=datetime(2026, 3, 3).date(),
                time=datetime.strptime('15:00', '%H:%M').time(),
                category='Art',
                location='Tampines West Community Centre',
                slots=18,
                host='Yong',
                image='default.png'
            ),
            Event(
                title='Yoga & Meditation for Relaxation',
                description='Find peace and flexibility through gentle yoga and guided meditation. Perfect for beginners and seniors. No equipment needed beyond a mat. Increase mobility and reduce stress!',
                date=datetime(2026, 3, 5).date(),
                time=datetime.strptime('08:30', '%H:%M').time(),
                category='Fitness',
                location='Clementi Community Centre',
                slots=30,
                host='Chen Hui',
                image='default.png'
            ),
            Event(
                title='Storytelling: Share Your Memoir',
                description='Ever wanted to preserve your life story? Join our storytelling session and share your most memorable moments. Others will listen, appreciate, and you\'ll create lasting memories together.',
                date=datetime(2026, 3, 8).date(),
                time=datetime.strptime('16:00', '%H:%M').time(),
                category='Social',
                location='Buona Vista Community Centre',
                slots=12,
                host='Margaret',
                image='default.png'
            ),
            Event(
                title='Ukulele for Seniors',
                description='Pick up a ukulele and play your favorite songs! Perfect instrument for beginners. Learn basic chords and strum some classics. Instruments available for rent if you don\'t have one.',
                date=datetime(2026, 3, 10).date(),
                time=datetime.strptime('14:00', '%H:%M').time(),
                category='Music',
                location='Serangoon Community Club',
                slots=16,
                host='Lim Wei',
                image='default.png'
            ),
            Event(
                title='Woodworking: Build a Bird House',
                description='Learn basic woodworking by building a beautiful bird house! All tools and materials provided. Take home your creation and attract birds to your garden.',
                date=datetime(2026, 3, 12).date(),
                time=datetime.strptime('10:00', '%H:%M').time(),
                category='Craft',
                location='MacPherson Community Centre',
                slots=14,
                host='Yong',
                image='default.png'
            )
        ]
        
        for event in sample_events:
            db.session.add(event)
        
        db.session.commit()
        print("Database seeded with sample events!")
            
    db.session.commit()
    print("Database seeded with Hobbies and Interests!")

# --- INITIALIZE DB ---
with app.app_context():
    db.create_all()
    seed_data()

# --- STORY DATA STRUCTURE (In-memory) ---
_id_counter = itertools.count(1)
user_stories = [
    {
        "id": next(_id_counter),
        "title": "Sunset at Marina Bay",
        "description": "Caught the golden hour—added a timelapse clip.",
        "media": [],
        "date": "2026-01-10",
        "tags": ["Travel", "Photography"],
        "privacy": "Public",
        "likes": 12,
        "comments": [
            {"author": "Ava", "text": "Beautiful colors!"},
            {"author": "Ken", "text": "Timelapse is smooth."}
        ],
        "saved": False,
        "reported": False,
        "author": "Yong"
    },
    {
        "id": next(_id_counter),
        "title": "First Flask App",
        "description": "Built a small app with Bootstrap and WTForms.",
        "media": [],
        "date": "2026-01-12",
        "tags": ["Tech", "Learning"],
        "privacy": "Public",
        "likes": 7,
        "comments": [{"author": "Mia", "text": "Nice progress!"}],
        "saved": True,
        "reported": False,
        "author": "Yong"
    },
    {
        "id": next(_id_counter),
        "title": "Weekend Hike at Bukit Timah",
        "description": "Conquered the summit trail at Bukit Timah Nature Reserve today! The climb was challenging but the view from the top was absolutely worth it.",
        "media": [],
        "date": "2026-01-13",
        "tags": ["Travel", "Nature", "Lifestyle"],
        "privacy": "Public",
        "likes": 15,
        "comments": [
            {"author": "Jake", "text": "Great photos! I should go hiking more."},
            {"author": "Sarah", "text": "The trail looks amazing!"}
        ],
        "saved": False,
        "reported": False,
        "author": "Yong"
    },
    {
        "id": next(_id_counter),
        "title": "Morning Tai Chi at East Coast Park",
        "description": "Started my day with a peaceful tai chi session by the beach. The morning breeze and sound of waves made it even more relaxing.",
        "media": [],
        "date": "2026-01-15",
        "tags": ["Lifestyle", "Health", "Seniors"],
        "privacy": "Public",
        "likes": 24,
        "comments": [
            {"author": "Margaret", "text": "I should join you next time!"},
            {"author": "Robert", "text": "Great way to start the day."}
        ],
        "saved": False,
        "reported": False,
        "author": "Lim Wei"
    },
    {
        "id": next(_id_counter),
        "title": "Grandma's Secret Chicken Rice Recipe",
        "description": "Spent the afternoon learning my grandmother's famous Hainanese chicken rice recipe. She shared tips passed down from her mother.",
        "media": ["uploads/chicken_rice.avif"],
        "date": "2026-01-14",
        "tags": ["Food", "Family", "Seniors"],
        "privacy": "Public",
        "likes": 31,
        "comments": [
            {"author": "Sarah", "text": "Please share the recipe!"},
            {"author": "David", "text": "Family recipes are precious treasures."}
        ],
        "saved": False,
        "reported": False,
        "author": "Chen Hui"
    },
    {
        "id": next(_id_counter),
        "title": "My First Day on BridgeGen",
        "description": "Just joined this amazing community platform! Excited to connect with people from different generations and share our stories.",
        "media": [],
        "date": "2026-01-20",
        "tags": ["Lifestyle", "Community"],
        "privacy": "Public",
        "likes": 8,
        "comments": [
            {"author": "Yong", "text": "Welcome to the community!"},
            {"author": "Lim Wei", "text": "Glad to have you here!"}
        ],
        "saved": False,
        "reported": False,
        "author": "yongen"
    },
    {
        "id": next(_id_counter),
        "title": "Building BridgeGen Platform",
        "description": "Working on a full-stack Flask application for my web development project. Implementing user authentication, stories, events, and community features. It's challenging but rewarding!",
        "media": [],
        "date": "2026-01-22",
        "tags": ["Tech", "Learning", "Projects"],
        "privacy": "Public",
        "likes": 15,
        "comments": [
            {"author": "Yong", "text": "Flask is powerful, keep it up!"},
            {"author": "Mia", "text": "Can't wait to see the final product!"}
        ],
        "saved": True,
        "reported": False,
        "author": "yongen"
    },
    {
        "id": next(_id_counter),
        "title": "Coffee Study Session at NP",
        "description": "Pulled an all-nighter at the library preparing for my IT project presentation. Coffee is my best friend right now!",
        "media": [],
        "date": "2026-01-23",
        "tags": ["Education", "Lifestyle"],
        "privacy": "Public",
        "likes": 12,
        "comments": [
            {"author": "Jake", "text": "Good luck with your presentation!"},
            {"author": "Sarah", "text": "You got this!"}
        ],
        "saved": False,
        "reported": False,
        "author": "yongen"
    },
    {
        "id": next(_id_counter),
        "title": "Weekend Gaming Marathon",
        "description": "Finally beat that boss I've been stuck on for weeks! Gaming is such a great way to unwind after a long week of coding.",
        "media": [],
        "date": "2026-01-24",
        "tags": ["Gaming", "Lifestyle", "Entertainment"],
        "privacy": "Public",
        "likes": 20,
        "comments": [
            {"author": "Ken", "text": "Which game?"},
            {"author": "David", "text": "Gaming and coding go hand in hand!"}
        ],
        "saved": True,
        "reported": False,
        "author": "yongen"
    },
    {
        "id": next(_id_counter),
        "title": "Learning Python for Web Development",
        "description": "Deep diving into Flask, SQLAlchemy, and building RESTful APIs. The learning curve is steep but I'm making steady progress every day.",
        "media": [],
        "date": "2026-01-25",
        "tags": ["Tech", "Learning", "Programming"],
        "privacy": "Public",
        "likes": 18,
        "comments": [
            {"author": "Yong", "text": "Python is a great choice!"},
            {"author": "Mia", "text": "Keep up the great work!"}
        ],
        "saved": True,
        "reported": False,
        "author": "yongen"
    },
]

def get_recommended_stories(user=None):
    """Get recommended stories for a user based on their tags"""
    if not user:
        return sorted(user_stories, key=lambda x: x["likes"], reverse=True)[:4]
    
    username = user.username if hasattr(user, 'username') else str(user)
    user_tags = set(t for s in user_stories if s.get("author") == username for t in s.get("tags", []))
    rec = []
    for s in user_stories:
        if s.get("author") != username and (user_tags & set(s.get("tags", []))):
            rec.append(s)
    
    if not rec:
        rec = sorted(user_stories, key=lambda x: x["likes"], reverse=True)[:4]
    return rec[:4]

# --- ROUTES ---

@app.route('/')
def home():
    return render_template('home.html', user=current_user)

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        action = request.form.get('action')
        
        # --- REGISTER ---
        if action == 'register':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            
            if User.query.filter_by(email=email).first():
                flash('Email already exists.', 'danger')
            elif User.query.filter_by(username=username).first():
                flash('Username already taken.', 'danger')
            else:
                new_user = User(username=username, email=email)
                new_user.set_password(password)
                db.session.add(new_user)
                db.session.commit()
                
                login_user(new_user, remember=False) # Auto login after register
                flash(f'Welcome, {username}!', 'success')
                return redirect(url_for('home'))

        # --- LOGIN ---
        elif action == 'login':
            email = request.form.get('email')
            password = request.form.get('password')
            remember = request.form.get('remember') == 'on'
            user = User.query.filter_by(email=email).first()
            
            if user and user.check_password(password):
                login_user(user, remember=remember) # Use remember checkbox value
                flash('Welcome back!', 'success')
                return redirect(url_for('home'))
            else:
                flash('Login Failed. Check email or password.', 'danger')

    return render_template('auth.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))



@app.route('/add_friend_by_id', methods=['POST'])
@login_required
def add_friend_by_id():
    target_id = request.form.get('friend_id')
    
    if not target_id or not target_id.isdigit():
        flash('Please enter a valid numeric ID.', 'danger')
        return redirect(url_for('profile'))
        
    friend = User.query.get(int(target_id))
    
    if not friend:
        flash('User not found. Check the ID and try again.', 'danger')
    elif friend.id == current_user.id:
        flash('You cannot add yourself!', 'warning')
    elif current_user.is_friend(friend):
        flash(f'You are already connected with {friend.username}.', 'info')
    else:
        current_user.add_friend(friend)
        notif = Notification(message=f"{current_user.username} added you via ID!", user_id=friend.id)
        db.session.add(notif)
        db.session.commit()
        flash(f'Success! You are now connected with {friend.username}.', 'success')
        
    return redirect(url_for('profile'))

@app.route('/connect/<int:user_id>')
@login_required
def connect_user(user_id):
    user_to_add = User.query.get_or_404(user_id)
    
    if current_user == user_to_add:
        flash('You cannot connect with yourself!', 'warning')
    elif current_user.is_friend(user_to_add):
        flash(f'You are already connected with {user_to_add.username}.', 'info')
    else:
        current_user.add_friend(user_to_add)
        msg = f"{current_user.username} started following you!"
        notif = Notification(message=msg, user_id=user_to_add.id)
        db.session.add(notif)
        db.session.commit()
        flash(f'You are now connected with {user_to_add.username}!', 'success')
        
    return redirect(url_for('community'))

@app.route('/disconnect/<int:user_id>')
@login_required
def disconnect_user(user_id):
    user_to_remove = User.query.get_or_404(user_id)
    current_user.remove_friend(user_to_remove)
    db.session.commit()
    flash(f'Disconnected from {user_to_remove.username}.', 'info')
    return redirect(url_for('community'))

@app.route('/chat')
@login_required
def chat():
    messages = ChatMessage.query.order_by(ChatMessage.timestamp.desc()).limit(50).all()
    messages = messages[::-1]
    return render_template('chat.html', user=current_user, messages=messages)

@app.route('/chat/messaging')
@login_required
def chat_messaging():
    """Real-time chat messaging page - Only show friends"""
    
    # Get user's actual friends (not all users)
    friends = current_user.friends.all()
    
    # For the "new chat" modal, also show only friends
    all_users = friends
    
    return render_template('chat.html', user=current_user, friends=friends, all_users=all_users)
@app.route('/chat/upload', methods=['POST'])
@login_required
def chat_upload_file():
    """Handle file upload for chat messages"""
    try:
        print("=== FILE UPLOAD REQUEST ===")
        print("Form data:", request.form)
        print("Files:", request.files)
        
        # Check if file is in request
        if 'file' not in request.files:
            print("ERROR: No file in request")
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400
        
        file = request.files['file']
        receiver_id = request.form.get('receiver_id')
        message_text = request.form.get('message', '')
        
        print(f"File: {file.filename}")
        print(f"Receiver ID: {receiver_id}")
        print(f"Message: {message_text}")
        
        # Check if filename is empty
        if file.filename == '':
            print("ERROR: Empty filename")
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Validate receiver_id
        if not receiver_id:
            print("ERROR: No receiver ID")
            return jsonify({
                'success': False,
                'error': 'No receiver specified'
            }), 400
        
        # Check file size (10MB limit)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
        if file_size > MAX_FILE_SIZE:
            print("ERROR: File too large")
            return jsonify({
                'success': False,
                'error': 'File size exceeds 10MB limit'
            }), 400
        
        # Generate secure filename
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        
        # Create uploads directory if it doesn't exist
        upload_folder = os.path.join(app.root_path, 'css', 'uploads', 'chat')
        os.makedirs(upload_folder, exist_ok=True)
        
        # Save file
        filepath = os.path.join(upload_folder, unique_filename)
        print(f"Saving to: {filepath}")
        file.save(filepath)
        
        # Generate URL for file access
        file_url = f"/css/uploads/chat/{unique_filename}"
        
        print(f"File saved successfully: {file_url}")
        
        # Create message record in database
        new_message = Message(
            sender_id=current_user.id,
            receiver_id=int(receiver_id),
            message=message_text if message_text else None,
            attachment_url=file_url,
            attachment_name=filename,
            attachment_type=file.content_type,
            attachment_size=file_size,
            timestamp=datetime.utcnow()
        )
        
        db.session.add(new_message)
        db.session.commit()
        
        print(f"Message saved to database: ID {new_message.id}")
        
        # Prepare message data for socket emission
        message_data = new_message.to_dict()
        
        # Emit to receiver via Socket.IO
        if int(receiver_id) in active_users:
            socketio.emit('receive_message', message_data, room=f'user_{receiver_id}')
        
        # Also emit to sender (for multiple devices/tabs)
        socketio.emit('receive_message', message_data, room=f'user_{current_user.id}')
        
        print("Socket events emitted successfully")
        
        return jsonify({
            'success': True,
            'message': message_data
        }), 200
        
    except Exception as e:
        print(f"ERROR in chat_upload_file: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500
@app.route('/chat/message/<int:message_id>/edit', methods=['PUT'])
@login_required
def edit_message(message_id):
    """Edit a message"""
    try:
        # Get the message
        message = Message.query.get(message_id)
        
        if not message:
            return jsonify({'success': False, 'error': 'Message not found'}), 404
        
        # Check if user owns the message
        if message.sender_id != current_user.id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Get new message text
        data = request.get_json()
        new_text = data.get('message', '').strip()
        
        if not new_text:
            return jsonify({'success': False, 'error': 'Message cannot be empty'}), 400
        
        # Cannot edit messages with attachments
        if message.attachment_url:
            return jsonify({'success': False, 'error': 'Cannot edit messages with attachments'}), 400
        
        # Update message
        message.message = new_text
        message.edited = True
        message.edited_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': {
                'id': message.id,
                'message': message.message,
                'edited': True,
                'edited_at': message.edited_at.isoformat()
            }
        }), 200
        
    except Exception as e:
        print(f"Error editing message: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/chat/history/<int:user_id>')
@login_required
def chat_history(user_id):
    """Get chat history between current user and specified user"""
    current_user_id = current_user.id
    
    messages = Message.query.filter(
        db.or_(
            db.and_(Message.sender_id == current_user_id, Message.receiver_id == user_id),
            db.and_(Message.sender_id == user_id, Message.receiver_id == current_user_id)
        )
    ).order_by(Message.timestamp.asc()).all()
    
    Message.query.filter(
        Message.sender_id == user_id,
        Message.receiver_id == current_user_id,
        Message.is_read == False
    ).update({'is_read': True})
    db.session.commit()
    
    return jsonify({'messages': [msg.to_dict() for msg in messages]})

@app.route('/chat/unread-count')
@login_required
def unread_count():
    """Get unread message counts"""
    # ============================================================
# MESSAGE DELETE ROUTE
# ============================================================

@app.route('/chat/message/<int:message_id>/delete', methods=['DELETE'])
@login_required
def delete_message(message_id):
    """Delete a message"""
    try:
        # Get the message
        message = Message.query.get(message_id)
        
        if not message:
            return jsonify({'success': False, 'error': 'Message not found'}), 404
        
        # Check if user owns the message
        if message.sender_id != current_user.id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Delete attached file if exists
        if message.attachment_url:
            try:
                # Remove leading slash if present
                file_path = message.attachment_url.lstrip('/')
                full_path = os.path.join(app.root_path, file_path)
                if os.path.exists(full_path):
                    os.remove(full_path)
                    print(f"Deleted file: {full_path}")
            except Exception as file_error:
                print(f"Error deleting file: {file_error}")
        
        # Delete message from database
        db.session.delete(message)
        db.session.commit()
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        print(f"Error deleting message: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# CLEAR CHAT HISTORY ROUTE
# ============================================================

@app.route('/chat/clear/<int:user_id>', methods=['DELETE'])
@login_required
def clear_chat_history(user_id):
    """Clear all messages with a specific user"""
    try:
        # Get all messages between current user and specified user
        messages = Message.query.filter(
            db.or_(
                db.and_(
                    Message.sender_id == current_user.id,
                    Message.receiver_id == user_id
                ),
                db.and_(
                    Message.sender_id == user_id,
                    Message.receiver_id == current_user.id
                )
            )
        ).all()
        
        # Delete attached files
        for message in messages:
            if message.attachment_url:
                try:
                    file_path = message.attachment_url.lstrip('/')
                    full_path = os.path.join(app.root_path, file_path)
                    if os.path.exists(full_path):
                        os.remove(full_path)
                except Exception as file_error:
                    print(f"Error deleting file: {file_error}")
        
        # Delete all messages
        Message.query.filter(
            db.or_(
                db.and_(
                    Message.sender_id == current_user.id,
                    Message.receiver_id == user_id
                ),
                db.and_(
                    Message.sender_id == user_id,
                    Message.receiver_id == current_user.id
                )
            )
        ).delete()
        
        db.session.commit()
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        print(f"Error clearing chat: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# REMOVE FRIEND ROUTE
# ============================================================

@app.route('/remove_friend/<int:friend_id>', methods=['POST'])
@login_required
def remove_friend(friend_id):
    """Remove a friend"""
    try:
        # Get the friend user
        friend = User.query.get(friend_id)
        
        if not friend:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Check if they are friends
        if not current_user.is_friend(friend):
            return jsonify({'success': False, 'error': 'Not friends'}), 400
        
        # Remove friendship (this should handle bidirectional removal)
        current_user.remove_friend(friend)
        db.session.commit()
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        print(f"Error removing friend: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@socketio.on('send_old_message')
def handle_old_message(data):
    username = data['username']
    message_content = data['message']
    
    new_msg = ChatMessage(username=username, message=message_content)
    db.session.add(new_msg)
    db.session.commit()
    
    emit('receive_message', {'username': username, 'message': message_content}, broadcast=True)


@app.route('/events')
def events():
    """Redirect to the new event browse page"""
    return redirect(url_for('event_browse'))

@app.route('/story')
def story():
    """Redirect to the new story home page"""
    return redirect(url_for('story_home'))

@app.route('/community')
@login_required
def community():
    """Redirect to communities page"""
    return redirect(url_for('community_home'))

@app.route('/notifications')
@login_required
def notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.timestamp.desc()).all()
    return render_template('notifications.html', notifications=notifs, user=current_user)

@app.route('/profile')
@login_required
def profile():
    user_interest_names = [i.name for i in current_user.interests]
    return render_template('profile.html', user=current_user, user_interest_names=user_interest_names)

@app.route('/forgot_password')
def forgot_password():
    return render_template('forgot_password.html', user=None)

@app.route('/update_color', methods=['POST'])
@login_required
def update_color():
    color = request.form.get('color')
    if color:
        current_user.background_color = color
        db.session.commit()
        flash('Background color updated!', 'success')
    
    return redirect(url_for('profile'))


# --- HOBBIES & INTERESTS ROUTES ---

@app.route('/hobbies')
@login_required
def hobbies():
    return render_template('hobbies.html', user=current_user)

@app.route('/save_hobbies', methods=['POST'])
@login_required
def save_hobbies():
    selected_names = request.form.getlist('hobbies')
    other_hobby = request.form.get('other_hobby') 
    
    if other_hobby:
        other_hobby = other_hobby.strip().title()
        if other_hobby:
            selected_names.append(other_hobby)
            if not Hobby.query.filter_by(name=other_hobby).first():
                db.session.add(Hobby(name=other_hobby))
                db.session.commit()

    current_user.hobbies = [] 
    for name in selected_names:
        hobby_obj = Hobby.query.filter_by(name=name).first()
        if hobby_obj:
            current_user.hobbies.append(hobby_obj)
            
    db.session.commit()
    flash('Hobbies updated!', 'success')
    return redirect(url_for('profile'))

# --- CHANGE USERNAME ROUTES ---
@app.route('/change_username', methods=['GET', 'POST'])
@login_required
def change_username():
    if request.method == 'POST':
        new_username = request.form.get('new_username')
        if User.query.filter_by(username=new_username).first():
            flash('This username is already taken.', 'danger')
        else:
            current_user.username = new_username
            db.session.commit()
            return render_template('success_action.html', 
                                   message="Username Updated!", 
                                   sub_message="Your new username is set.",
                                   btn_text="Back to Profile",
                                   redirect_url=url_for('profile'))

    return render_template('change_username.html', user=current_user)

# --- CHANGE EMAIL ROUTES ---
@app.route('/change_email', methods=['GET', 'POST'])
@login_required
def change_email():
    if request.method == 'POST':
        new_email = request.form.get('new_email')
        if User.query.filter_by(email=new_email).first():
            flash('This email is already in use.', 'danger')
        else:
            current_user.email = new_email
            db.session.commit()
            return render_template('success_action.html', 
                                   message="Email Updated!", 
                                   sub_message="Your email has been changed.",
                                   btn_text="Back to Profile",
                                   redirect_url=url_for('profile'))

    return render_template('change_email.html', user=current_user)

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    # 1. Update DOB
    d = request.form.get('dob_d')
    m = request.form.get('dob_m')
    y = request.form.get('dob_y')
    if d and m and y:
        current_user.dob = f"{d}-{m}-{y}"

    # 2. Update Interests
    selected_interests_str = request.form.get('selected_interests')
    if selected_interests_str is not None: 
        current_user.interests = [] # Clear old
        if selected_interests_str: 
            interest_names = selected_interests_str.split(',')
            for name in interest_names:
                interest = Interest.query.filter_by(name=name).first()
                if not interest:
                    interest = Interest(name=name)
                current_user.interests.append(interest)

    try:
        db.session.commit()
        flash('Profile updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating profile: {e}', 'error')

    return redirect(url_for('profile'))


@app.route('/choose_profile_pic', methods=['GET', 'POST'])
@login_required
def choose_profile_pic():
    if request.method == 'POST':
        selected_avatar = request.form.get('avatar')
        if selected_avatar:
            current_user.profile_pic = selected_avatar
            db.session.commit()
            # Success Page
            return render_template('success_action.html', 
                                   message="SUCCESS!", 
                                   sub_message="Your Profile Picture has been saved",
                                   btn_text="MyProfile",
                                   redirect_url=url_for('profile'))

    return render_template('choose_profile_pic.html', user=current_user)


@app.route('/upload_profile_pic', methods=['POST'])
@login_required
def upload_profile_pic():
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('choose_profile_pic'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('choose_profile_pic'))

    if file:
        filename = secure_filename(file.filename)
        upload_folder = os.path.join(app.root_path, 'css', 'uploads')
        
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
            
        file.save(os.path.join(upload_folder, filename))
        
        current_user.profile_pic = f"/css/uploads/{filename}"
        db.session.commit()
        
        flash('Profile picture uploaded!', 'success')
        return redirect(url_for('profile'))

    return redirect(url_for('choose_profile_pic'))


@app.route('/update_profile_pic', methods=['POST'])
@login_required
def update_profile_pic():
    avatar_url = request.form.get('avatar_url')
    if avatar_url:
        current_user.profile_pic = avatar_url
        db.session.commit()
        flash('Avatar updated!', 'success')
    return redirect(url_for('profile'))

@app.route('/remove_profile_pic')
@login_required
def remove_profile_pic():
    # Reset to a default "Initials" avatar based on their username
    default_pic = f"https://api.dicebear.com/7.x/initials/svg?seed={current_user.username}"
    
    current_user.profile_pic = default_pic
    db.session.commit()
    
    flash('Profile picture removed.', 'info')
    return redirect(url_for('profile'))


@app.route('/delete_account', methods=['GET', 'POST'])
@login_required
def delete_account():
    if request.method == 'POST':
        db.session.delete(current_user)
        db.session.commit()
        logout_user()
        return render_template('success_action.html', 
                               message="Successfully Deleted!", 
                               sub_message="You have deleted your account you may go back to Homepage",
                               btn_text="Homepage",
                               redirect_url=url_for('home'))

    return render_template('delete_account.html', user=current_user)

@app.route('/settings')
def settings():
    return render_template('base.html')

# ========== NEW EVENT ROUTES ==========

@app.route('/events/browse')
def event_browse():
    """Browse all events with search and filter"""
    q = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    query = Event.query
    if q:
        query = query.filter(Event.title.ilike(f'%{q}%'))
    if category:
        query = query.filter(Event.category == category)
    events = query.order_by(Event.date.asc(), Event.time.asc()).all()
    
    joined_ids = set()
    if current_user.is_authenticated:
        joined_ids = {p.event_id for p in EventParticipant.query.filter_by(user_id=current_user.id).all()}
    
    return render_template('event_browse.html', events=events, joined_ids=joined_ids, q=q, category=category, user=current_user if current_user.is_authenticated else None)

@app.route('/events/<int:event_id>')
def event_details(event_id):
    """View event details"""
    event = Event.query.get_or_404(event_id)
    joined = False
    is_creator = False
    if current_user.is_authenticated:
        joined = EventParticipant.query.filter_by(user_id=current_user.id, event_id=event.id).first() is not None
        is_creator = event.host == current_user.username
    return render_template('event_details.html', event=event, joined=joined, is_creator=is_creator, user=current_user if current_user.is_authenticated else None)

@app.route('/events/create', methods=['GET', 'POST'])
@login_required
def event_create():
    """Create a new event"""
    form = EventForm()
    
    if form.validate_on_submit():
        filename = None
        if form.image.data:
            uploads_dir = os.path.join(app.root_path, 'css', 'uploads')
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
            host=current_user.username,
            image=filename
        )
        db.session.add(event)
        db.session.commit()

        # Automatically add creator as participant
        participant = EventParticipant(user_id=current_user.id, event_id=event.id)
        db.session.add(participant)
        db.session.commit()

        flash('Event created and you have been added as a participant.', 'success')
        return redirect(url_for('event_details', event_id=event.id))
    
    return render_template('event_create.html', form=form, user=current_user)

@app.route('/events/<int:event_id>/edit', methods=['GET', 'POST'])
@login_required
def event_edit(event_id):
    """Edit an existing event"""
    event = Event.query.get_or_404(event_id)
    
    if event.host != current_user.username:
        flash('Only the event creator can edit this event.', 'warning')
        return redirect(url_for('event_browse'))

    form = EventForm(obj=event)

    if form.validate_on_submit():
        if form.image.data:
            uploads_dir = os.path.join(app.root_path, 'css', 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            orig = secure_filename(getattr(form.image.data, 'filename', ''))
            if orig:
                ext = os.path.splitext(orig)[1]
                filename = f"{uuid.uuid4().hex}{ext}"
                form.image.data.save(os.path.join(uploads_dir, filename))
                
                try:
                    if event.image and event.image != 'default.png':
                        old_path = os.path.join(uploads_dir, event.image)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                except Exception:
                    pass
                event.image = filename

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

    return render_template('event_edit.html', form=form, event=event, user=current_user)

@app.route('/events/<int:event_id>/delete', methods=['POST'])
@login_required
def event_delete(event_id):
    """Delete an event"""
    event = Event.query.get_or_404(event_id)
    
    if event.host != current_user.username:
        flash('Only the event creator can delete this event.', 'warning')
        return redirect(url_for('event_browse'))
    
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted.', 'info')
    return redirect(url_for('event_browse'))

@app.route('/events/<int:event_id>/join', methods=['POST'])
@login_required
def event_join(event_id):
    """Join an event"""
    event = Event.query.get_or_404(event_id)
    existing = EventParticipant.query.filter_by(user_id=current_user.id, event_id=event.id).first()
    if not existing:
        db.session.add(EventParticipant(user_id=current_user.id, event_id=event.id))
        db.session.commit()
        flash('You joined the event.', 'success')

    dest = request.referrer or url_for('event_browse')
    return redirect(dest)

@app.route('/events/<int:event_id>/leave', methods=['POST'])
@login_required
def event_leave(event_id):
    """Leave an event"""
    part = EventParticipant.query.filter_by(user_id=current_user.id, event_id=event_id).first()
    if part:
        db.session.delete(part)
        db.session.commit()
        flash('You left the event.', 'info')

    dest = request.referrer or url_for('event_browse')
    return redirect(dest)

@app.route('/events/my-events')
@login_required
def event_my_events():
    """View user's events with calendar"""
    # All joined events (including those the user created)
    joined_all = (db.session.query(Event)
                  .join(EventParticipant, Event.id == EventParticipant.event_id)
                  .filter(EventParticipant.user_id == current_user.id)
                  .order_by(Event.date.asc(), Event.time.asc())
                  .all())

    # Joined events (exclude those where user is the host)
    joined = [e for e in joined_all if e.host != current_user.username]

    # Created events
    created = Event.query.filter(Event.host == current_user.username).order_by(Event.date.asc()).all()

    # Calendar month/year selection
    try:
        sel_month = int(request.args.get('month', datetime.utcnow().month))
        sel_year = int(request.args.get('year', datetime.utcnow().year))
    except ValueError:
        sel_month = datetime.utcnow().month
        sel_year = datetime.utcnow().year

    num_days = calendar.monthrange(sel_year, sel_month)[1]
    first_weekday = calendar.monthrange(sel_year, sel_month)[0]
    leading_blanks = first_weekday

    # Use joined_all for calendar highlights
    joined_in_month = [e for e in joined_all if e.date.month == sel_month and e.date.year == sel_year]
    joined_days = {e.date.day for e in joined_in_month}

    # Reflections (attended) for joined events in selected month
    joined_event_ids = [e.id for e in joined_in_month]
    attended_days = set()
    if joined_event_ids:
        attended = Reflection.query.filter(Reflection.user_id == current_user.id, Reflection.event_id.in_(joined_event_ids)).all()
        attended_event_ids = {r.event_id for r in attended}
        events_map = {e.id: e for e in joined_in_month}
        for eid in attended_event_ids:
            ev = events_map.get(eid)
            if ev:
                attended_days.add(ev.date.day)

    # Prev/next month links
    if sel_month == 1:
        prev_month, prev_year = 12, sel_year - 1
    else:
        prev_month, prev_year = sel_month - 1, sel_year
    if sel_month == 12:
        next_month, next_year = 1, sel_year + 1
    else:
        next_month, next_year = sel_month + 1, sel_year

    month_name = calendar.month_name[sel_month]

    return render_template('event_my_events.html',
                           joined=joined,
                           created=created,
                           sel_month=sel_month,
                           sel_year=sel_year,
                           month_name=month_name,
                           num_days=num_days,
                           leading_blanks=leading_blanks,
                           joined_days=joined_days,
                           attended_days=attended_days,
                           prev_month=prev_month,
                           prev_year=prev_year,
                           next_month=next_month,
                           next_year=next_year,
                           user=current_user)

@app.route('/events/reflection/<int:event_id>', methods=['GET', 'POST'])
@login_required
def event_reflection(event_id):
    """Submit a reflection for an event"""
    event = Event.query.get_or_404(event_id)
    
    # Allow reflection if user joined OR is the event host
    participant = EventParticipant.query.filter_by(user_id=current_user.id, event_id=event.id).first()
    if not participant and event.host != current_user.username:
        flash('Only participants or the event creator can submit reflections.', 'warning')
        return redirect(url_for('event_browse'))

    form = ReflectionForm()
    existing = Reflection.query.filter_by(user_id=current_user.id, event_id=event.id).first()

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
            existing.submitted_at = datetime.utcnow()
        else:
            new_ref = Reflection(
                user_id=current_user.id,
                event_id=event.id,
                rating=form.rating.data,
                comments=form.comments.data,
                submitted_at=datetime.utcnow()
            )
            db.session.add(new_ref)
        db.session.commit()
        flash('Reflection submitted.', 'success')
        return redirect(url_for('event_my_events'))

    return render_template('event_reflection.html', form=form, event=event, user=current_user)

@app.route('/events/reflection/creator/<int:event_id>', methods=['GET', 'POST'])
@login_required
def event_creator_reflection(event_id):
    """Submit a creator reflection for an event"""
    event = Event.query.get_or_404(event_id)
    
    if event.host != current_user.username:
        flash('Only the event creator can submit a creator reflection here.', 'warning')
        return redirect(url_for('event_browse'))

    form = CreatorReflectionForm()
    existing = Reflection.query.filter_by(user_id=current_user.id, event_id=event.id).first()

    if request.method == 'GET' and existing:
        form.rating.data = existing.rating
        form.comments.data = existing.comments

    if form.validate_on_submit():
        if existing:
            existing.rating = form.rating.data
            existing.comments = form.comments.data
            existing.submitted_at = datetime.utcnow()
            db.session.commit()
            flash('You have updated your post reflection.', 'success')
        else:
            new_ref = Reflection(
                user_id=current_user.id,
                event_id=event.id,
                rating=form.rating.data,
                comments=form.comments.data,
                submitted_at=datetime.utcnow()
            )
            db.session.add(new_ref)
            db.session.commit()
            flash('You have submitted your post reflection.', 'success')
        return redirect(url_for('event_my_events'))

    return render_template('event_creator_reflection.html', form=form, event=event, user=current_user)

# ========== END EVENT ROUTES ==========

# ========== NEW STORY ROUTES ==========

@app.route('/story/home')
@login_required
def story_home():
    """Story home page with user's stories and recommendations"""
    username = current_user.username
    my_stories = [s for s in user_stories if s.get("author") == username][:4]
    recommended = get_recommended_stories(current_user)
    return render_template('story_home.html', my_stories=my_stories, recommended=recommended, user=current_user)

@app.route('/story/browse')
@login_required
def story_browse():
    """Browse all stories with search and filter"""
    q = request.args.get("q", "").strip().lower()
    tag = request.args.get("tag", "").strip()
    filtered = user_stories
    if q:
        filtered = [s for s in filtered if q in s["title"].lower() or q in s["description"].lower()]
    if tag:
        filtered = [s for s in filtered if tag in s["tags"]]
    tags = sorted({t for s in user_stories for t in s["tags"]})
    return render_template('story_browse.html', stories=filtered, tags=tags, q=q, selected_tag=tag, user=current_user)

@app.route('/story/details/<int:story_id>', methods=['GET', 'POST'])
@login_required
def story_details(story_id):
    """View details of a story (others' stories)"""
    s = next((x for x in user_stories if x["id"] == story_id), None)
    if not s:
        flash("Story not found.", "warning")
        return redirect(url_for('story_browse'))
    
    if request.method == 'POST':
        action = request.form.get("action")
        if action == "like":
            s["likes"] += 1
        elif action == "save":
            s["saved"] = not s.get("saved", False)
        elif action == "report":
            s["reported"] = True
            flash("Story reported.", "info")
        elif action == "comment":
            author = request.form.get("author", current_user.username).strip() or current_user.username
            text = request.form.get("text", "").strip()
            if text:
                s["comments"].append({"author": author, "text": text})
        return redirect(url_for('story_details', story_id=story_id))
    
    return render_template('story_details.html', story=s, user=current_user)

@app.route('/story/my-story/<int:story_id>', methods=['GET', 'POST'])
@login_required
def story_my_story(story_id):
    """View user's own story"""
    s = next((x for x in user_stories if x["id"] == story_id), None)
    if not s:
        flash("Story not found.", "warning")
        return redirect(url_for('story_my_stories'))
    if s.get("author") != current_user.username:
        flash("You can only view your own stories from this page.", "warning")
        return redirect(url_for('story_details', story_id=story_id))
    
    if request.method == 'POST':
        action = request.form.get("action")
        if action == "comment":
            author = request.form.get("author", current_user.username).strip() or current_user.username
            text = request.form.get("text", "").strip()
            if text:
                s["comments"].append({"author": author, "text": text})
        return redirect(url_for('story_my_story', story_id=story_id))
    
    return render_template('story_my_story.html', story=s, user=current_user)

@app.route('/story/create', methods=['GET', 'POST'])
@login_required
def story_create():
    """Create a new story"""
    if request.method == 'POST':
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        privacy = request.form.get("privacy", "").strip()
        
        if not title or not description or not privacy:
            flash("Title, description, and privacy setting are required.", "warning")
            tag_options = ["Travel", "Photography", "Tech", "Learning", "Food", "Lifestyle", "Art"]
            return render_template('story_create.html', tag_options=tag_options, user=current_user)
        
        selected_tags = request.form.getlist("tags")
        custom_tags_str = request.form.get("custom_tags", "").strip()
        custom_tags = [tag.strip() for tag in custom_tags_str.split(",") if tag.strip()]
        tags = list(set(selected_tags + custom_tags))
        
        if not selected_tags:
            flash("Please select at least one predefined tag.", "warning")
            tag_options = ["Travel", "Photography", "Tech", "Learning", "Food", "Lifestyle", "Art"]
            return render_template('story_create.html', tag_options=tag_options, user=current_user)
        
        voiceRecording = request.form.get("voiceRecording")
        media_files = request.files.getlist("media")
        
        media = []
        for file in media_files:
            if file.filename:
                upload_folder = os.path.join(app.root_path, 'css', 'uploads')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                filename = secure_filename(file.filename)
                file.save(os.path.join(upload_folder, filename))
                media.append("uploads/" + filename)
        
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        story = {
            "id": next(_id_counter),
            "title": title,
            "description": description,
            "tags": tags,
            "date": current_date,
            "privacy": privacy,
            "likes": 0,
            "comments": [],
            "media": media,
            "voice": voiceRecording,
            "author": current_user.username,
            "saved": False,
            "reported": False
        }
        user_stories.append(story)
        return redirect(url_for('story_confirm_post', story_id=story["id"]))
    
    tag_options = ["Travel", "Photography", "Tech", "Learning", "Food", "Lifestyle", "Art"]
    return render_template('story_create.html', tag_options=tag_options, user=current_user)

@app.route('/story/confirm-post/<int:story_id>', methods=['GET', 'POST'])
@login_required
def story_confirm_post(story_id):
    """Confirm post before finalizing"""
    s = next((x for x in user_stories if x["id"] == story_id), None)
    if not s:
        flash("Story not found.", "warning")
        return redirect(url_for('story_create'))
    return render_template('story_confirm_post.html', story=s, user=current_user)

@app.route('/story/finalize-post/<int:story_id>', methods=['POST'])
@login_required
def story_finalize_post(story_id):
    """Finalize the post"""
    s = next((x for x in user_stories if x["id"] == story_id), None)
    if not s:
        flash("Story not found.", "warning")
        return redirect(url_for('story_create'))
    flash("Story posted successfully!", "success")
    return redirect(url_for('story_my_stories'))

@app.route('/story/edit/<int:story_id>', methods=['GET', 'POST'])
@login_required
def story_edit(story_id):
    """Edit an existing story"""
    s = next((x for x in user_stories if x["id"] == story_id), None)
    if not s:
        flash("Story not found.", "warning")
        return redirect(url_for('story_my_stories'))
    if s.get("author") != current_user.username:
        flash("You can only edit your own stories.", "warning")
        return redirect(url_for('story_details', story_id=story_id))
    
    if request.method == 'POST':
        s["title"] = request.form.get("title", s["title"]).strip() or s["title"]
        s["description"] = request.form.get("description", s["description"]).strip() or s["description"]
        s["date"] = request.form.get("date", s["date"]) or s["date"]
        
        selected_tags = request.form.getlist("tags")
        custom_tags_str = request.form.get("custom_tags", "").strip()
        custom_tags = [tag.strip() for tag in custom_tags_str.split(",") if tag.strip()]
        s["tags"] = list(set(selected_tags + custom_tags)) or s["tags"]
        
        s["privacy"] = request.form.get("privacy", s["privacy"]) or s["privacy"]
        
        media_files = request.files.getlist("media")
        existing_media = request.form.getlist("existing_media")
        
        media = [m for m in existing_media if m.strip()]
        
        for file in media_files:
            if file.filename:
                upload_folder = os.path.join(app.root_path, 'css', 'uploads')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                filename = secure_filename(file.filename)
                file.save(os.path.join(upload_folder, filename))
                media.append("uploads/" + filename)
        
        s["media"] = media
        return redirect(url_for('story_confirm_save', story_id=story_id))
    
    tag_options = ["Travel", "Photography", "Tech", "Learning", "Food", "Lifestyle", "Art"]
    return render_template('story_edit.html', story=s, tag_options=tag_options, user=current_user)

@app.route('/story/confirm-save/<int:story_id>')
@login_required
def story_confirm_save(story_id):
    """Confirm save after editing"""
    s = next((x for x in user_stories if x["id"] == story_id), None)
    if not s:
        flash("Story not found.", "warning")
        return redirect(url_for('story_my_stories'))
    flash("Story saved successfully!", "success")
    return render_template('story_confirm_save.html', story=s, user=current_user)

@app.route('/story/my-stories')
@login_required
def story_my_stories():
    """View all user's stories"""
    q = request.args.get("q", "").strip().lower()
    tag = request.args.get("tag", "").strip()
    mine = [s for s in user_stories if s.get("author") == current_user.username]
    if q:
        mine = [s for s in mine if q in s["title"].lower() or q in s["description"].lower()]
    if tag:
        mine = [s for s in mine if tag in s["tags"]]
    tags = sorted({t for s in user_stories if s.get("author") == current_user.username for t in s["tags"]})
    return render_template('story_my_stories.html', stories=mine, tags=tags, q=q, selected_tag=tag, user=current_user)

@app.route('/story/delete/<int:story_id>', methods=['GET', 'POST'])
@login_required
def story_delete(story_id):
    """Delete a story"""
    s = next((x for x in user_stories if x["id"] == story_id), None)
    if not s:
        flash("Story not found.", "warning")
        return redirect(url_for('story_my_stories'))
    
    if request.method == 'POST':
        confirm = request.form.get("confirm")
        if confirm == "yes":
            idx = next((i for i, x in enumerate(user_stories) if x["id"] == story_id), None)
            if idx is not None:
                user_stories.pop(idx)
            flash("Story deleted successfully.", "success")
            return redirect(url_for('story_my_stories'))
        else:
            return redirect(url_for('story_my_stories'))
    
    return render_template('story_confirm_delete.html', story=s, pending=True, user=current_user)

@app.route('/story/confirm-delete')
@login_required
def story_confirm_delete():
    """Confirm deletion"""
    return render_template('story_confirm_delete.html', story=None, pending=False, user=current_user)

# ========== END STORY ROUTES ==========

# ========== COMMUNITY ROUTES ==========

@app.route('/communities')
@login_required
def community_home():
    """Browse all communities with search and filter"""
    search = request.args.get('search', '')
    category = request.args.get('category', 'all')
    
    # Base query
    query = Community.query
    if search:
        query = query.filter((Community.name.contains(search)) | (Community.description.contains(search)))
    if category != 'all':
        query = query.filter_by(category=category)
    
    all_communities = query.all()
    
    # Get user's communities
    user_memberships = CommunityMember.query.filter_by(user_id=current_user.id).all()
    user_community_ids = [m.community_id for m in user_memberships]
    
    # Split communities
    my_communities = [c for c in all_communities if c.id in user_community_ids]
    discover_communities = [c for c in all_communities if c.id not in user_community_ids]
    
    return render_template('community_communities.html',
                         my_communities=my_communities,
                         discover_communities=discover_communities,
                         search=search,
                         category=category,
                         user=current_user)

@app.route('/communities/<int:community_id>')
@login_required
def community_detail(community_id):
    """View community details with posts, members, and events"""
    community = Community.query.get_or_404(community_id)
    is_member = CommunityMember.query.filter_by(
        user_id=current_user.id,
        community_id=community_id
    ).first() is not None
    is_creator = community.creator_id == current_user.id
    
    upcoming_events = CommunityEvent.query.filter_by(community_id=community_id).filter(CommunityEvent.date_time >= datetime.utcnow()).order_by(CommunityEvent.date_time).all()
    
    # Get posts with comment counts and like status
    posts = Post.query.filter_by(community_id=community_id).order_by(Post.created_at.desc()).all()
    for post in posts:
        post.user_has_liked = PostLike.query.filter_by(user_id=current_user.id, post_id=post.id).first() is not None
        
    # Get members
    memberships = CommunityMember.query.filter_by(community_id=community_id).all()
    members = []
    for m in memberships:
        user = User.query.get(m.user_id)
        user.role = m.role
        # Check friendship status
        is_friend = current_user.is_friend(user) if user.id != current_user.id else False
        user.is_friend_status = is_friend
        members.append(user)

    return render_template('community_community_detail.html',
                         community=community,
                         is_member=is_member,
                         is_creator=is_creator,
                         upcoming_events=upcoming_events,
                         posts=posts,
                         members=members,
                         user=current_user)

@app.route('/communities/<int:community_id>/posts/create', methods=['POST'])
@login_required
def community_create_post(community_id):
    """Create a post in a community"""
    if not CommunityMember.query.filter_by(user_id=current_user.id, community_id=community_id).first():
        flash('You must be a member to post.', 'error')
        return redirect(url_for('community_detail', community_id=community_id))
        
    content = request.form.get('content')
    image = request.files.get('image')
    
    if not content and not image:
        flash('Post cannot be empty', 'error')
        return redirect(url_for('community_detail', community_id=community_id))
        
    filename = None
    if image and image.filename:
        uploads_dir = os.path.join(app.root_path, 'css', 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        filename = secure_filename(f"{datetime.now().timestamp()}_{image.filename}")
        image.save(os.path.join(uploads_dir, filename))
        
    post = Post(
        content=content,
        image_filename=filename,
        user_id=current_user.id,
        community_id=community_id
    )
    db.session.add(post)
    db.session.commit()
    
    flash('Post created!', 'success')
    return redirect(url_for('community_detail', community_id=community_id))

@app.route('/posts/<int:post_id>/like', methods=['POST'])
@login_required
def community_like_post(post_id):
    """Toggle like on a post"""
    post = Post.query.get_or_404(post_id)
    like = PostLike.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    
    if like:
        db.session.delete(like)
        action = 'unliked'
    else:
        like = PostLike(user_id=current_user.id, post_id=post_id)
        db.session.add(like)
        action = 'liked'
        
    db.session.commit()
    return jsonify({'status': 'success', 'action': action, 'count': post.like_count})

@app.route('/posts/<int:post_id>/comment', methods=['POST'])
@login_required
def community_add_comment(post_id):
    """Add a comment to a post"""
    content = request.form.get('content')
    if not content:
        flash('Comment cannot be empty', 'error')
        return redirect(request.referrer)
        
    comment = CommunityComment(
        content=content,
        user_id=current_user.id,
        post_id=post_id
    )
    db.session.add(comment)
    db.session.commit()
    
    return redirect(request.referrer)

@app.route('/communities/<int:community_id>/members/<int:user_id>/role', methods=['POST'])
@login_required
def community_toggle_role(community_id, user_id):
    """Toggle member role between admin and member"""
    community = Community.query.get_or_404(community_id)
    if community.creator_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    membership = CommunityMember.query.filter_by(community_id=community_id, user_id=user_id).first_or_404()
    
    new_role = request.json.get('role')
    if new_role in ['admin', 'member']:
        membership.role = new_role
        db.session.commit()
        return jsonify({'status': 'success'})
        
    return jsonify({'error': 'Invalid role'}), 400

@app.route('/communities/<int:community_id>/create-event', methods=['GET', 'POST'])
@login_required
def community_create_event(community_id):
    """Create an event for a community"""
    community = Community.query.get_or_404(community_id)
    
    if community.creator_id != current_user.id:
        flash('Only the community admin can create events.', 'error')
        return redirect(url_for('community_detail', community_id=community_id))
    
    if request.method == 'POST':
        date_str = request.form['date']
        time_str = request.form['time']
        dt_str = f"{date_str} {time_str}"
        try:
            event_date_time = datetime.strptime(dt_str, '%Y-%m-%d %H:%M')
        except ValueError:
            flash('Invalid date or time format', 'error')
            return render_template('community_create_event.html', community=community, user=current_user)
            
        event = CommunityEvent(
            title=request.form['title'],
            description=request.form['description'],
            date_time=event_date_time,
            location=request.form['location'],
            community_id=community_id
        )
        db.session.add(event)
        db.session.commit()
        flash('Event created successfully!', 'success')
        return redirect(url_for('community_detail', community_id=community_id))
        
    return render_template('community_create_event.html', community=community, user=current_user)

@app.route('/communities/<int:community_id>/join')
@login_required
def community_join(community_id):
    """Join a community"""
    if not CommunityMember.query.filter_by(user_id=current_user.id, community_id=community_id).first():
        membership = CommunityMember(user_id=current_user.id, community_id=community_id)
        db.session.add(membership)
        db.session.commit()
        flash('Joined community!', 'success')
    
    return redirect(url_for('community_detail', community_id=community_id))

@app.route('/communities/<int:community_id>/leave')
@login_required
def community_leave(community_id):
    """Leave a community"""
    membership = CommunityMember.query.filter_by(user_id=current_user.id, community_id=community_id).first()
    if membership:
        db.session.delete(membership)
        db.session.commit()
        flash('Left community', 'info')
    return redirect(url_for('community_home'))

@app.route('/communities/<int:community_id>/edit', methods=['GET', 'POST'])
@login_required
def community_edit(community_id):
    """Edit a community (creator only)"""
    community = Community.query.get_or_404(community_id)
    
    if community.creator_id != current_user.id:
        flash('Only the creator can edit this community.', 'danger')
        return redirect(url_for('community_detail', community_id=community_id))
    
    if request.method == 'POST':
        community.name = request.form['name']
        community.description = request.form['description']
        community.category = request.form['category']
        
        # Handle image upload
        image = request.files.get('image')
        if image and image.filename:
            uploads_dir = os.path.join(app.root_path, 'css', 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            filename = secure_filename(f"community_{datetime.now().timestamp()}_{image.filename}")
            image.save(os.path.join(uploads_dir, filename))
            community.image_filename = filename
        
        db.session.commit()
        flash('Community updated!', 'success')
        return redirect(url_for('community_detail', community_id=community_id))
    
    return render_template('community_edit_community.html', community=community, user=current_user)

@app.route('/communities/<int:community_id>/delete', methods=['POST'])
@login_required
def community_delete(community_id):
    """Delete a community"""
    community = Community.query.get_or_404(community_id)
    
    if community.creator_id != current_user.id:
        flash('You can only delete communities you created', 'error')
        return redirect(url_for('community_detail', community_id=community_id))
    
    CommunityMember.query.filter_by(community_id=community_id).delete()
    db.session.delete(community)
    db.session.commit()
    
    flash('Community deleted successfully', 'success')
    return redirect(url_for('community_home'))

@app.route('/create-community', methods=['GET', 'POST'])
@login_required
def community_create():
    """Create a new community"""
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        category = request.form['category']
        image = request.files.get('image')

        filename = None
        if image and image.filename:
            uploads_dir = os.path.join(app.root_path, 'css', 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            filename = secure_filename(f"community_{datetime.now().timestamp()}_{image.filename}")
            image.save(os.path.join(uploads_dir, filename))
        
        community = Community(
            name=name,
            description=description,
            category=category,
            image_filename=filename,
            creator_id=current_user.id
        )
        db.session.add(community)
        db.session.commit()
        
        # Auto-join as creator
        membership = CommunityMember(
            user_id=current_user.id, 
            community_id=community.id,
            role='admin'
        )
        db.session.add(membership)
        db.session.commit()
        
        flash('Community created!', 'success')
        return redirect(url_for('community_detail', community_id=community.id))
    
    return render_template('community_create_community.html', user=current_user)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    uploads_dir = os.path.join(app.root_path, 'css', 'uploads')
    return send_from_directory(uploads_dir, filename)

@app.route('/users/<int:user_id>/add-friend', methods=['POST'])
@login_required
def add_friend(user_id):
    """Add a user as friend"""
    if user_id == current_user.id:
        return jsonify({'error': 'Cannot add yourself'}), 400
        
    # Check if already friends
    friend = User.query.get(user_id)
    if friend and current_user.is_friend(friend):
        return jsonify({'status': 'already_friends'})
    
    # Add friend
    if friend:
        current_user.add_friend(friend)
        db.session.commit()
        return jsonify({'status': 'success'})
    
    return jsonify({'error': 'User not found'}), 404

# ========== END COMMUNITY ROUTES ==========

# ========== CHATBOT ROUTE ==========

@app.route('/chatbot', methods=['POST'])
@login_required
def chatbot():
    """Simple rule-based chatbot for assistance"""
    user_message = request.json.get('message', '')
    if not user_message:
        return jsonify({'response': 'Please send a message.'})
    
    message_lower = user_message.lower()
    
    # Greetings
    if any(word in message_lower for word in ['hello', 'hi', 'hey', 'greetings']):
        return jsonify({'response': "Hello! I'm your BridgeGen assistant. How can I help you today? I can help you with communities, events, stories, or answer questions about the platform."})
    
    # Community questions
    if any(word in message_lower for word in ['community', 'communities', 'join', 'find']):
        return jsonify({'response': "To find communities, go to the Community page and browse. You can search by name or filter by category. Click 'Join' on any community that interests you!"})
    
    # Event questions
    if any(word in message_lower for word in ['event', 'events', 'activities']):
        return jsonify({'response': "Visit the Events page to browse all events. You can filter by category, search by name, and join events that interest you. Create your own events to connect with others!"})
    
    # Story questions
    if any(word in message_lower for word in ['story', 'stories', 'share']):
        return jsonify({'response': "Share your stories on the Story page! You can add text, photos, voice recordings, and tags. Your stories help bridge generations and create connections."})
    
    # Help
    if any(word in message_lower for word in ['help', 'assist', 'support', 'how']):
        return jsonify({'response': "I can help you with: communities, events, stories, navigation, and general questions about BridgeGen. What would you like to know?"})
    
    # Features
    if any(word in message_lower for word in ['feature', 'features', 'what can', 'what does']):
        return jsonify({'response': "BridgeGen connects youth and elders through communities, events, and stories. You can join communities, attend events, share stories, chat with friends, and build intergenerational connections!"})
    
    # Default response
    return jsonify({'response': "I'm here to help! You can ask me about communities, events, stories, or any questions about using BridgeGen. What would you like to know?"})

# ========== END CHATBOT ROUTE ==========
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f'Client disconnected: {request.sid}')
    for user_id, sid in list(active_users.items()):
        if sid == request.sid:
            del active_users[user_id]
            break

@socketio.on('join')
def handle_join(data):
    """User joins their personal room"""
    username = data.get('username')
    if current_user.is_authenticated:
        user_id = current_user.id
        session['user_id'] = user_id  # Store in session for other handlers
        active_users[user_id] = request.sid
        join_room(f'user_{user_id}')
        print(f'User {username} (ID: {user_id}) joined their room')

@socketio.on('send_message')
def handle_send_message_new(data):
    """Handle sending a message (new chat system)"""
    try:
        sender_id = current_user.id if current_user.is_authenticated else session.get('user_id')

        receiver_id = data.get('receiver_id')
        message_text = data.get('message')
        
        if not all([sender_id, receiver_id, message_text]):
            emit('error', {'message': 'Invalid message data'})
            return
        
        message = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            message=message_text,
            timestamp=datetime.utcnow()
        )
        db.session.add(message)
        db.session.commit()
        
        # ✅ USE to_dict() instead of manually creating dictionary
        message_data = message.to_dict()
        
        # Send to receiver's room
        if receiver_id in active_users:
            socketio.emit('receive_message', message_data, room=f'user_{receiver_id}')
        
        # Send to sender (for confirmation)
        emit('receive_message', message_data)
        print(f'Message from {sender_id} to {receiver_id}: {message_text}')
        
    except Exception as e:
        print(f'Error sending message: {str(e)}')
        emit('error', {'message': 'Failed to send message'})

@socketio.on('typing')
def handle_typing(data):
    """Handle typing indicator"""
    user_id = data.get('user_id')
    sender_id = current_user.id if current_user.is_authenticated else session.get('user_id')
    
    if user_id in active_users:
        socketio.emit('user_typing', {'user_id': sender_id}, room=f'user_{user_id}')

@socketio.on('stop_typing')
def handle_stop_typing(data):
    """Handle stop typing indicator"""
    user_id = data.get('user_id')
    sender_id = current_user.id if current_user.is_authenticated else session.get('user_id')

    
    if user_id in active_users:
        socketio.emit('user_stop_typing', {'user_id': sender_id}, room=f'user_{user_id}')
@socketio.on('message_edited')
def handle_message_edited(data):
    """Handle message edited event"""
    try:
        message_id = data.get('message_id')
        new_text = data.get('new_text')
        receiver_id = data.get('receiver_id')
        
        print(f"Message edited: {message_id}, receiver: {receiver_id}")
        
        # Emit to receiver
        if receiver_id in active_users:
            socketio.emit('message_edited', {
                'message_id': message_id,
                'new_text': new_text
            }, room=f'user_{receiver_id}')
        
    except Exception as e:
        print(f"Error handling message_edited event: {e}")


@socketio.on('message_deleted')
def handle_message_deleted(data):
    """Handle message deleted event"""
    try:
        message_id = data.get('message_id')
        receiver_id = data.get('receiver_id')
        
        print(f"Message deleted: {message_id}, receiver: {receiver_id}")
        
        # Emit to receiver
        if receiver_id in active_users:
            socketio.emit('message_deleted', {
                'message_id': message_id
            }, room=f'user_{receiver_id}')
        
    except Exception as e:
        print(f"Error handling message_deleted event: {e}")
if __name__ == '__main__':
    socketio.run(app, debug=True)