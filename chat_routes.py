from flask import render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime
from app import app, db  # Import from your main app file
from models import User  # Import your User model

# Initialize SocketIO (add this to your main app.py if not already there)
# socketio = SocketIO(app, cors_allowed_origins="*")

# Message Model - Add this to your models.py file
class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    
    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')
    
    def to_dict(self):
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'is_read': self.is_read
        }

# Store active users
active_users = {}

# ==========================================
# CHAT ROUTES
# ==========================================

@app.route('/chat')
def chat():
    """Main chat page"""
    if 'user_id' not in session:
        return redirect(url_for('auth'))
    
    user = User.query.get(session['user_id'])
    
    # Get user's friends for contact list
    # If you have a friends relationship, use: friends = user.friends
    # Otherwise, get all users except current user
    friends = User.query.filter(User.id != user.id).all()
    
    # Get all users for new chat modal
    all_users = User.query.filter(User.id != user.id).all()
    
    return render_template('chat.html', user=user, friends=friends, all_users=all_users)

@app.route('/chat/history/<int:user_id>')
def chat_history(user_id):
    """Get chat history between current user and specified user"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    current_user_id = session['user_id']
    
    # Get messages between current user and the specified user
    messages = Message.query.filter(
        db.or_(
            db.and_(Message.sender_id == current_user_id, Message.receiver_id == user_id),
            db.and_(Message.sender_id == user_id, Message.receiver_id == current_user_id)
        )
    ).order_by(Message.timestamp.asc()).all()
    
    # Mark messages as read
    Message.query.filter(
        Message.sender_id == user_id,
        Message.receiver_id == current_user_id,
        Message.is_read == False
    ).update({'is_read': True})
    db.session.commit()
    
    return jsonify({
        'messages': [msg.to_dict() for msg in messages]
    })

@app.route('/chat/unread-count')
def unread_count():
    """Get unread message counts"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    
    # Get unread message count per sender
    unread_counts = db.session.query(
        Message.sender_id,
        db.func.count(Message.id).label('count')
    ).filter(
        Message.receiver_id == user_id,
        Message.is_read == False
    ).group_by(Message.sender_id).all()
    
    return jsonify({
        'unread': {str(sender_id): count for sender_id, count in unread_counts}
    })

# ==========================================
# SOCKET.IO EVENTS
# ==========================================
# Note: Import socketio from your main app file where you initialized it

from app import socketio  # Import socketio from wherever you initialized it

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f'Client disconnected: {request.sid}')
    # Remove from active users
    for user_id, sid in list(active_users.items()):
        if sid == request.sid:
            del active_users[user_id]
            break

@socketio.on('join')
def handle_join(data):
    """User joins their personal room"""
    username = data.get('username')
    if 'user_id' in session:
        user_id = session['user_id']
        active_users[user_id] = request.sid
        join_room(f'user_{user_id}')
        print(f'User {username} (ID: {user_id}) joined their room')

@socketio.on('send_message')
def handle_send_message(data):
    """Handle sending a message"""
    try:
        sender_id = session.get('user_id')
        receiver_id = data.get('receiver_id')
        message_text = data.get('message')
        
        if not all([sender_id, receiver_id, message_text]):
            emit('error', {'message': 'Invalid message data'})
            return
        
        # Save message to database
        message = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            message=message_text,
            timestamp=datetime.utcnow()
        )
        db.session.add(message)
        db.session.commit()
        
        # Prepare message data
        message_data = {
            'id': message.id,
            'sender_id': sender_id,
            'receiver_id': receiver_id,
            'message': message_text,
            'timestamp': message.timestamp.isoformat()
        }
        
        # Send to receiver if they're online
        if receiver_id in active_users:
            socketio.emit('receive_message', message_data, room=f'user_{receiver_id}')
        
        # Send confirmation back to sender
        emit('receive_message', message_data)
        
        print(f'Message from {sender_id} to {receiver_id}: {message_text}')
        
    except Exception as e:
        print(f'Error sending message: {str(e)}')
        emit('error', {'message': 'Failed to send message'})

@socketio.on('typing')
def handle_typing(data):
    """Handle typing indicator"""
    user_id = data.get('user_id')
    sender_id = session.get('user_id')
    
    if user_id in active_users:
        socketio.emit('user_typing', {'user_id': sender_id}, room=f'user_{user_id}')

@socketio.on('stop_typing')
def handle_stop_typing(data):
    """Handle stop typing indicator"""
    user_id = data.get('user_id')
    sender_id = session.get('user_id')
    
    if user_id in active_users:
        socketio.emit('user_stop_typing', {'user_id': sender_id}, room=f'user_{user_id}')