from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date, time
from werkzeug.security import generate_password_hash, check_password_hash
import pytz

db = SQLAlchemy()

# Singapore timezone constant
SINGAPORE_TZ = pytz.timezone('Asia/Singapore')

# --- 1. ASSOCIATION TABLES ---
connections = db.Table('connections',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('friend_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

user_hobbies = db.Table('user_hobbies',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('hobby_id', db.Integer, db.ForeignKey('hobby.id'), primary_key=True)
)

user_interests = db.Table('user_interests',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('interest_id', db.Integer, db.ForeignKey('interest.id'), primary_key=True)
)

# --- 2. THE USER MODEL ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    dob = db.Column(db.String(20))
    profile_pic = db.Column(db.String(150), default='default.png')
    
    # Store the hashed password
    _password_hash = db.Column(db.String(150), nullable=False)
    
    background_color = db.Column(db.String(20), default='#f8f9fa')

    # Relationships
    friends = db.relationship(
        'User', secondary=connections,
        primaryjoin=(connections.c.user_id == id),
        secondaryjoin=(connections.c.friend_id == id),
        backref=db.backref('followers', lazy='dynamic'), 
        lazy='dynamic'
    )

    hobbies = db.relationship('Hobby', secondary=user_hobbies, backref='users')
    interests = db.relationship('Interest', secondary=user_interests, backref='users')

    # --- PASSWORD LOGIC (The Fix) ---
    
    # This is the function your app.py is calling!
    def set_password(self, password):
        self._password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self._password_hash, password)

    # (Optional) Property setter if you want to use new_user.password = 'xyz'
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self._password_hash = generate_password_hash(password)

    # --- HELPER METHODS ---
    def is_friend(self, user):
        return self.friends.filter(connections.c.friend_id == user.id).count() > 0

    def add_friend(self, user):
        if not self.is_friend(user):
            self.friends.append(user)

    def remove_friend(self, user):
        if self.is_friend(user):
            self.friends.remove(user)

# --- HELPER FUNCTION FOR SINGAPORE TIME ---
def get_singapore_time():
    """Get current time in Singapore timezone"""
    return datetime.now(SINGAPORE_TZ)

def utc_to_singapore(utc_dt):
    """Convert UTC datetime to Singapore timezone"""
    if utc_dt.tzinfo is None:
        # If datetime is naive (no timezone), assume it's UTC
        utc_dt = pytz.utc.localize(utc_dt)
    return utc_dt.astimezone(SINGAPORE_TZ)

# --- 3. OTHER MODELS ---
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    slots = db.Column(db.Integer, nullable=False)
    host = db.Column(db.String(80), nullable=False)  # host username
    image = db.Column(db.String(200), nullable=True)

class EventParticipant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)

class Reflection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1–5
    comments = db.Column(db.Text, nullable=False)
    submitted_at = db.Column(db.DateTime, nullable=False)

class Story(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, nullable=True)
    media = db.Column(db.String(500), nullable=True)  # Comma-separated filenames
    voice_recording = db.Column(db.String(200), nullable=True)
    tags = db.Column(db.String(300), nullable=True)  # Comma-separated tags
    privacy = db.Column(db.String(20), nullable=False, default='Public')
    likes = db.Column(db.Integer, default=0)
    saved = db.Column(db.Boolean, default=False)
    reported = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', backref='stories')

class StoryComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'), nullable=False)
    author = db.Column(db.String(80), nullable=False)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    story = db.relationship('Story', backref='comments')

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Hobby(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class Interest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

# --- COMMUNITY MODELS ---
class Community(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    image_filename = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    @property
    def member_count(self):
        return CommunityMember.query.filter_by(community_id=self.id).count()

class CommunityMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    community_id = db.Column(db.Integer, db.ForeignKey('community.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.String(20), default='member')  # 'admin', 'member'

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    community_id = db.Column(db.Integer, db.ForeignKey('community.id'), nullable=False)
    
    author = db.relationship('User', backref='posts')
    
    @property
    def like_count(self):
        return PostLike.query.filter_by(post_id=self.id).count()

class CommunityComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    
    author = db.relationship('User', backref='community_comments')
    post = db.relationship('Post', backref='comments')

class PostLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

class CommunityEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date_time = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    community_id = db.Column(db.Integer, db.ForeignKey('community.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# --- MESSAGE MODEL FOR ONE-ON-ONE CHAT ---
class Message(db.Model):
    """Model for one-on-one chat messages with file attachments and edit support"""
    __tablename__ = 'message'  # Changed from 'messages' to match your app.py
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Message text - MUST BE NULLABLE for file-only messages
    message = db.Column(db.Text, nullable=True)
    
    # ✅ FILE ATTACHMENT FIELDS (NEW)
    attachment_url = db.Column(db.String(500), nullable=True)
    attachment_name = db.Column(db.String(255), nullable=True)
    attachment_type = db.Column(db.String(100), nullable=True)
    attachment_size = db.Column(db.Integer, nullable=True)
    
    # ✅ MESSAGE EDIT TRACKING FIELDS (NEW)
    edited = db.Column(db.Boolean, default=False)
    edited_at = db.Column(db.DateTime, nullable=True)
    
    # Store as UTC in database, but will convert to Singapore time when sending to frontend
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    
    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')
    
    def to_dict(self):
        """Convert message to dictionary for JSON serialization
        
        Returns timestamp as ISO 8601 string with UTC timezone indicator,
        which JavaScript can properly parse and convert to any timezone.
        Includes attachment and edit information.
        """
        # Ensure timestamp has UTC timezone info
        if self.timestamp.tzinfo is None:
            # If stored as naive datetime, assume it's UTC
            utc_time = pytz.utc.localize(self.timestamp)
        else:
            utc_time = self.timestamp
        
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'message': self.message,
            
            # ✅ ATTACHMENT FIELDS (NEW)
            'attachment_url': self.attachment_url,
            'attachment_name': self.attachment_name,
            'attachment_type': self.attachment_type,
            'attachment_size': self.attachment_size,
            
            # ✅ EDIT TRACKING FIELDS (NEW)
            'edited': self.edited,
            'edited_at': self.edited_at.isoformat() if self.edited_at else None,
            
            # Return ISO format with 'Z' suffix to indicate UTC
            'timestamp': utc_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'is_read': self.is_read
        }
    
    def __repr__(self):
        return f'<Message {self.id}: {self.sender_id} -> {self.receiver_id}>'