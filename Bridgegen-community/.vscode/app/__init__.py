from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_migrate import Migrate
from config import Config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
bootstrap = Bootstrap()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    bootstrap.init_app(app)
    migrate.init_app(app, db)
    
    # Configure login
    login_manager.login_view = 'main.login'
    login_manager.login_message_category = 'info'
    
    # Register blueprints
    from app.routes import main, community, chatbot, moderation, accessibility
    app.register_blueprint(main.bp)
    app.register_blueprint(community.bp)
    app.register_blueprint(chatbot.bp)
    app.register_blueprint(moderation.bp)
    app.register_blueprint(accessibility.bp)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app