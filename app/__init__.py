from flask import Flask
from .config import Config
from .database import init_db
from .routes import register_blueprints
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(Config)

    init_db(app)
    register_blueprints(app)

    return app
# Expose the Flask app instance
app = create_app()

from app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

