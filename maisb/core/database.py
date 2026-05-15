"""
Database configuration and session management
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
import os
import logging

logger = logging.getLogger(__name__)

# Database URL from environment or default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./maisb_enterprise.db"
)

# Create engine with appropriate settings
if "sqlite" in DATABASE_URL:
    # SQLite configuration for development
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
else:
    # PostgreSQL or other production database
    engine = create_engine(
        DATABASE_URL,
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",
        pool_size=20,
        max_overflow=40,
        pool_recycle=3600
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """
    Initialize database - creates all tables
    Call this on application startup
    """
    try:
        from maisb.core.models.tenant import Base
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

def get_db() -> Session:
    """
    FastAPI dependency for getting database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_session() -> Session:
    """
    Context manager for getting database session
    
    Usage:
        with get_db_session() as db:
            # do something with db
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
