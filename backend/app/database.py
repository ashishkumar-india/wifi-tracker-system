"""
Database connection and session management using SQLAlchemy.
Supports MySQL through XAMPP.
"""

from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,  # Recycle connections after 30 minutes
    echo=settings.DEBUG,
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.
    Yields a session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    Use with 'with' statement for explicit session management.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Database transaction error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """
    Initialize database tables.
    Creates all tables defined in models if they don't exist.
    """
    try:
        # Import all models to ensure they're registered
        from app.models import user, device, scan_result, alert, ml_prediction
        
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def check_db_connection() -> bool:
    """
    Check if database connection is working.
    Returns True if connection is successful, False otherwise.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


# Event listener for connection debugging
@event.listens_for(engine, "connect")
def on_connect(dbapi_connection, connection_record):
    """Log when a new database connection is established."""
    logger.debug("New database connection established")


@event.listens_for(engine, "checkout")
def on_checkout(dbapi_connection, connection_record, connection_proxy):
    """Log when a connection is checked out from the pool."""
    logger.debug("Database connection checked out from pool")
