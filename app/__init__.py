from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from .config import Config
from .database import db
import logging
from logging.handlers import RotatingFileHandler
import os

csrf = CSRFProtect()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure logs directory exists
    if not os.path.exists('logs'):
        os.mkdir('logs')

    # Configure logging
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )
    
    # File handler for general logs
    file_handler = RotatingFileHandler(
        'logs/stockmonitor.log', 
        maxBytes=10240000,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # File handler for error logs
    error_file_handler = RotatingFileHandler(
        'logs/error.log',
        maxBytes=10240000,  # 10MB
        backupCount=10
    )
    error_file_handler.setFormatter(formatter)
    error_file_handler.setLevel(logging.ERROR)

    # Add handlers to the application logger
    app.logger.addHandler(file_handler)
    app.logger.addHandler(error_file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('StockMonitor startup')

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
    from app.routes import home_bp, dashboard_bp, stocks_bp, api_bp

    app.register_blueprint(home_bp)
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(stocks_bp, url_prefix='/stocks')
    app.register_blueprint(api_bp)
    # Register error handlers
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Server Error: {error}')
        return 'Internal Server Error', 500

    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.error(f'Not Found Error: {error}')
        return 'Not Found', 404

    return app

