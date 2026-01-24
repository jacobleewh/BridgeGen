from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///communities.db'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200))
    user_type = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Community(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/communities')
@login_required
def communities():
    search = request.args.get('search', '')
    category = request.args.get('category', 'all')
    
    # Base query
    query = Community.query
    if search:
        query = query.filter(Community.name.contains(search) | Community.description.contains(search))
    if category != 'all':
        query = query.filter_by(category=category)
    
    all_communities = query.all()
    
    # Get user's communities
    user_memberships = CommunityMember.query.filter_by(user_id=current_user.id).all()
    user_community_ids = [m.community_id for m in user_memberships]
    
    # Split communities
    my_communities = [c for c in all_communities if c.id in user_community_ids]
    discover_communities = [c for c in all_communities if c.id not in user_community_ids]
    
    return render_template('communities.html',
                         my_communities=my_communities,
                         discover_communities=discover_communities,
                         search=search,
                         category=category)

@app.route('/communities/<int:community_id>')
@login_required
def community_detail(community_id):
    community = Community.query.get_or_404(community_id)
    is_member = CommunityMember.query.filter_by(
        user_id=current_user.id,
        community_id=community_id
    ).first() is not None
    is_creator = community.creator_id == current_user.id
    
    return render_template('community_detail.html',
                         community=community,
                         is_member=is_member,
                         is_creator=is_creator)

@app.route('/communities/<int:community_id>/join')
@login_required
def join_community(community_id):
    # Check if already a member
    if not CommunityMember.query.filter_by(user_id=current_user.id, community_id=community_id).first():
        membership = CommunityMember(user_id=current_user.id, community_id=community_id)
        db.session.add(membership)
        db.session.commit()
        flash('Joined community!', 'success')
    
    return redirect(url_for('community_detail', community_id=community_id))

@app.route('/communities/<int:community_id>/leave')
@login_required
def leave_community(community_id):
    membership = CommunityMember.query.filter_by(user_id=current_user.id, community_id=community_id).first()
    if membership:
        db.session.delete(membership)
        db.session.commit()
        flash('Left community', 'info')
    return redirect(url_for('communities'))

@app.route('/communities/<int:community_id>/delete', methods=['POST'])
@login_required
def delete_community(community_id):
    community = Community.query.get_or_404(community_id)
    
    # Only creator can delete
    if community.creator_id != current_user.id:
        flash('You can only delete communities you created', 'error')
        return redirect(url_for('community_detail', community_id=community_id))
    
    # Delete all memberships first
    CommunityMember.query.filter_by(community_id=community_id).delete()
    
    # Delete the community
    db.session.delete(community)
    db.session.commit()
    
    flash('Community deleted successfully', 'success')
    return redirect(url_for('communities'))

@app.route('/create-community', methods=['GET', 'POST'])
@login_required
def create_community():
    if request.method == 'POST':
        community = Community(
            name=request.form['name'],
            description=request.form['description'],
            category=request.form['category'],
            creator_id=current_user.id
        )
        db.session.add(community)
        db.session.commit()
        
        # Auto-join as creator
        membership = CommunityMember(user_id=current_user.id, community_id=community.id)
        db.session.add(membership)
        db.session.commit()
        
        flash('Community created!', 'success')
        return redirect(url_for('community_detail', community_id=community.id))
    
    return render_template('create_community.html')

# Auth routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            return redirect(url_for('communities'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Check if username or email already exists
        if User.query.filter_by(username=request.form['username']).first():
            flash('Username already exists', 'error')
            return render_template('register.html')
        if User.query.filter_by(email=request.form['email']).first():
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        user = User(
            username=request.form['username'],
            email=request.form['email'],
            user_type=request.form['user_type']
        )
        user.set_password(request.form['password'])
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('Account created successfully!', 'success')
        return redirect(url_for('communities'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

# Simple AI Chatbot
def simple_chatbot_response(user_message):
    """Simple rule-based chatbot for community assistance"""
    message_lower = user_message.lower()
    
    # Greetings
    if any(word in message_lower for word in ['hello', 'hi', 'hey', 'greetings']):
        return "Hello! I'm your BridgeGen assistant. How can I help you today? I can help you find communities, explain features, or answer questions about the platform."
    
    # Community questions
    if any(word in message_lower for word in ['community', 'communities', 'join', 'find']):
        return "To find communities, go to the Communities page and browse the Discover tab. You can search by name or filter by category. Click 'Join' on any community that interests you!"
    
    # Create community
    if any(word in message_lower for word in ['create', 'make', 'new community', 'start']):
        return "To create a community, click the '+ Create Community' button on the Communities page. Fill in the name, description, and choose a category. Once created, you'll automatically be a member!"
    
    # Categories
    if any(word in message_lower for word in ['category', 'categories', 'types']):
        return "We have several community categories: Technology, Arts & Culture, Hobbies, Sports & Fitness, Education, and Social. You can filter communities by category on the Communities page."
    
    # Help
    if any(word in message_lower for word in ['help', 'assist', 'support', 'how']):
        return "I can help you with: finding communities, creating communities, understanding categories, navigation, and general questions about BridgeGen. What would you like to know?"
    
    # Features
    if any(word in message_lower for word in ['feature', 'features', 'what can', 'what does']):
        return "BridgeGen connects youth and elders through communities. You can join communities, create your own, interact with members, and build intergenerational connections. Explore the Communities page to get started!"
    
    # Default response
    return "I'm here to help! You can ask me about communities, how to join or create them, categories, or any questions about using BridgeGen. What would you like to know?"

@app.route('/chatbot', methods=['POST'])
@login_required
def chatbot():
    user_message = request.json.get('message', '')
    if not user_message:
        return jsonify({'response': 'Please send a message.'})
    
    response = simple_chatbot_response(user_message)
    return jsonify({'response': response})

# Initialize
with app.app_context():
    db.create_all()
    if not User.query.first():
        admin = User(username='admin', email='admin@example.com', user_type='youth')
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5002)