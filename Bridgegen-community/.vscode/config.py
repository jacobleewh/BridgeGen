import os
try:
    from dotenv import load_dotenv  # type: ignore
except ImportError:
    def load_dotenv():
        pass

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Accessibility defaults
    DEFAULT_FONT_SIZE = 'medium'
    DEFAULT_THEME = 'default'
    
    # Content moderation
    BANNED_KEYWORDS = [
        'hate', 'attack', 'kill', 'scam', 'fraud', 'bully',
        'racist', 'discriminat', 'harass', 'threat', 'suicide'
    ]
    
    # AI Settings (use environment variables)
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    GOOGLE_VISION_KEY = os.environ.get('GOOGLE_VISION_KEY', '')
    
    # File upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.path.join(basedir, 'app/static/uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}