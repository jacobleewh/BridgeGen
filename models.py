from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

# --- 1. ENCAPSULATION: User Class ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    # Private attribute for password hash
    _password_hash = db.Column(db.String(128))
    
    # Relationships
    posts = db.relationship('ContentItem', backref='author', lazy=True)
    notifications = db.relationship('Notification', backref='recipient', lazy=True)

    # Getter
    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute!')

    # Setter (Encapsulates the hashing logic)
    @password.setter
    def password(self, password):
        self._password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self._password_hash, password)

# --- 2. INHERITANCE: Parent Content Class ---
class ContentItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Polymorphic Setup
    type = db.Column(db.String(50))
    __mapper_args__ = {
        'polymorphic_identity': 'content_item',
        'polymorphic_on': type
    }

    # --- 3. POLYMORPHISM: Abstract Method ---
    def get_card_details(self):
        return "Generic Content"

# Child Class: Event
class Event(ContentItem):
    id = db.Column(db.Integer, db.ForeignKey('content_item.id'), primary_key=True)
    location = db.Column(db.String(100))
    event_date = db.Column(db.String(50))

    __mapper_args__ = {'polymorphic_identity': 'event'}

    # Overriding method
    def get_card_details(self):
        return f"📍 Location: {self.location} | 📅 Date: {self.event_date}"

# Child Class: Story
class Story(ContentItem):
    id = db.Column(db.Integer, db.ForeignKey('content_item.id'), primary_key=True)
    content = db.Column(db.Text)

    __mapper_args__ = {'polymorphic_identity': 'story'}

    # Overriding method
    def get_card_details(self):
        return f"📝 Story Snippet: {self.content[:50]}..."

# Chat Message Model
class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))
    message = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Notification Model
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)