from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from .config import Config
from .database import db
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

csrf = CSRFProtect()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    
    # Configure Flask-Login
    login_manager.login_view = 'home.login'
    login_manager.login_message_category = 'info'

    # Import models here to avoid circular imports
    from app.database.models import User, Stock

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from app.routes import home_bp, dashboard_bp
    
    app.register_blueprint(home_bp)
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')

    return app

