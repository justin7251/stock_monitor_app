from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import OperationalError
from sqlalchemy import text  # Import the text function
import time

db = SQLAlchemy()

def validate_database_connection(app):
    """Validate the database connection."""
    with app.app_context():
        try:
            # Use a connection to execute the query
            with db.engine.connect() as connection:
                connection.execute(text('SELECT 1'))  # Use text() for raw SQL
            print("Database connection validated successfully.")
        except OperationalError as e:
            print(f"Database connection failed: {e}")

def init_db(app):
    """Initialize the database."""
    db.init_app(app)
    validate_database_connection(app)  # Validate the database connection
    with app.app_context():
        retries = 5
        for i in range(retries):
            try:
                db.create_all()  # Create tables
                break  # Exit loop if successful
            except OperationalError as e:
                print(f"Database connection failed: {e}. Retrying in 5 seconds...")
                time.sleep(5)
        else:
            print("Failed to connect to the database after several attempts.")
