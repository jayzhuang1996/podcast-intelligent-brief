"""
Initialize database and create default user.

Run this once to set up the database:
    python scripts/init_db.py
"""

import sys
import os

# Add parent directory to path so we can import src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db.database import init_db, SessionLocal
from src.db.models import User

def create_default_user():
    """Create default user (id=1) for MVP."""
    db = SessionLocal()

    try:
        # Check if user already exists
        existing_user = db.query(User).filter_by(id=1).first()
        if existing_user:
            print("✅ Default user already exists")
            return

        # Create user
        user = User(
            id=1,
            email="user@example.com"
        )
        db.add(user)
        db.commit()

        print("✅ Created default user (id=1)")
        print(f"   Email: {user.email}")
        print("   Context will be collected via questionnaire on each generation")

    except Exception as e:
        print(f"❌ Error creating default user: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("🔨 Initializing database...")

    # Create tables
    init_db()

    # Create default user
    create_default_user()

    print("\n✅ Database setup complete!")
    print("   Database location: ./data/podcast.db")
    print("   Next step: Run 'uvicorn src.main:app --reload'")
