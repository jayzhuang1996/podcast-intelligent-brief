"""
Database connection and session management.

Why SQLAlchemy?
- ORM abstracts database (easy to migrate SQLite → PostgreSQL later)
- Type-safe queries (catch errors before runtime)
- Relationship handling (automatic joins)
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.db.models import Base
import os

# Database URL from environment or default to SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/podcast.db")

# Create engine
# Why check_same_thread=False? SQLite doesn't allow connections across threads by default
# FastAPI is async, so we need to disable this check
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False  # Set True to see SQL queries (debugging)
)

# Create session factory
# Why sessionmaker? Creates new database sessions for each request
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Create all database tables.

    Call this once at startup or via scripts/init_db.py
    """
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")


def get_db():
    """
    Dependency injection for FastAPI routes.

    Why this pattern?
    - Each request gets its own database session
    - Session automatically closes after request
    - Prevents database connection leaks

    Usage in FastAPI:
    ```python
    @router.get("/episodes")
    def get_episodes(db: Session = Depends(get_db)):
        return db.query(Episode).all()
    ```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
