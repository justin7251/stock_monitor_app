from app import create_app
from app.database import db
from app.database.models import User, Stock

def init_database():
    app = create_app()
    with app.app_context():
        try:
            # Drop all tables
            db.drop_all()
            print("Dropped all existing tables")
            
            # Create all tables
            db.create_all()
            print("Created all tables successfully")
            
        except Exception as e:
            print(f"Error initializing database: {e}")
            raise e

if __name__ == "__main__":
    init_database() 