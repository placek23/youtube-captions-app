"""
Database connection and session management for Vercel Postgres (Neon).

This module handles database connections optimized for serverless environments.
"""

import os
import time
from dotenv import load_dotenv
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy.exc import OperationalError, DBAPIError
from contextlib import contextmanager
import logging

# Load environment variables from .env file
load_dotenv(override=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection configuration
# Priority: POSTGRES_PRISMA_URL (pgBouncer) > DATABASE_URL > POSTGRES_URL
DATABASE_URL = (
    os.getenv('POSTGRES_PRISMA_URL') or
    os.getenv('DATABASE_URL') or
    os.getenv('POSTGRES_URL')
)

if not DATABASE_URL:
    raise ValueError(
        "Database URL not found! Please set one of the following environment variables:\n"
        "  - POSTGRES_PRISMA_URL (recommended for Vercel - pgBouncer connection pooling)\n"
        "  - DATABASE_URL\n"
        "  - POSTGRES_URL\n"
        "For Vercel Postgres, these variables are automatically set when you connect a database."
    )

# Log which connection string is being used (without exposing credentials)
if os.getenv('POSTGRES_PRISMA_URL'):
    logger.info("Using POSTGRES_PRISMA_URL (pgBouncer connection pooling)")
elif os.getenv('DATABASE_URL'):
    logger.info("Using DATABASE_URL")
else:
    logger.info("Using POSTGRES_URL")

# Serverless connection configuration
# Detect if running in Vercel environment
IS_VERCEL = os.getenv('VERCEL') == '1'

# Connection retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 0.5  # seconds

# Vercel Postgres (Neon) connection optimization
# Use NullPool for serverless to avoid connection pooling issues
# Connection pooling is handled by Vercel/Neon's pgBouncer (when using POSTGRES_PRISMA_URL)
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,  # No connection pooling for serverless
    echo=False,  # Set to True for SQL query debugging
    connect_args={
        'connect_timeout': 10,  # 10 second connection timeout
        'options': '-c timezone=utc',  # Use UTC timezone
        'keepalives': 1,  # Enable TCP keepalives
        'keepalives_idle': 30,  # Seconds before sending keepalive probes
        'keepalives_interval': 10,  # Seconds between keepalive probes
        'keepalives_count': 5  # Number of keepalive probes before connection is considered dead
    }
)

if IS_VERCEL:
    logger.info("Running in Vercel serverless environment")

# Alternative configuration with connection pooling (uncomment if needed for local dev)
# engine = create_engine(
#     DATABASE_URL,
#     poolclass=QueuePool,
#     pool_size=5,
#     max_overflow=10,
#     pool_pre_ping=True,  # Verify connections before using
#     pool_recycle=300,  # Recycle connections after 5 minutes
#     echo=False
# )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Scoped session for thread-safe access
ScopedSession = scoped_session(SessionLocal)


def retry_on_db_error(func):
    """
    Decorator to retry database operations on connection errors.
    Useful for handling cold starts and transient connection issues.
    """
    def wrapper(*args, **kwargs):
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except (OperationalError, DBAPIError) as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY * (2 ** attempt)  # Exponential backoff
                    logger.warning(
                        f"Database operation failed (attempt {attempt + 1}/{MAX_RETRIES}). "
                        f"Retrying in {wait_time}s... Error: {e}"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"Database operation failed after {MAX_RETRIES} attempts: {e}")
        raise last_error
    return wrapper


def get_db():
    """
    Dependency for getting database session.

    Yields:
        Session: SQLAlchemy database session.

    Usage:
        with get_db() as db:
            # Use db session
            pass
    """
    db = ScopedSession()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        db.close()


@contextmanager
def get_db_session():
    """
    Context manager for database session.

    Usage:
        with get_db_session() as session:
            # Use session
            result = session.query(Model).all()
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


@retry_on_db_error
def test_connection():
    """
    Test database connection with retry logic.

    This function is decorated with retry logic to handle cold starts
    and transient connection issues in serverless environments.

    Returns:
        bool: True if connection successful, False otherwise.
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            result.fetchone()
            logger.info("✓ Database connection successful!")
            logger.info(f"  Connected to: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'database'}")
            return True
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        raise  # Re-raise to allow retry decorator to work


def get_database_info():
    """
    Get database information (version, name, etc.).

    Returns:
        dict: Database information.
    """
    try:
        with engine.connect() as connection:
            # Get PostgreSQL version
            version_result = connection.execute(text("SELECT version()"))
            version = version_result.fetchone()[0]

            # Get current database name
            db_result = connection.execute(text("SELECT current_database()"))
            db_name = db_result.fetchone()[0]

            # Get current user
            user_result = connection.execute(text("SELECT current_user"))
            user = user_result.fetchone()[0]

            return {
                'version': version,
                'database': db_name,
                'user': user,
                'url': DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'database'
            }
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        return None


def close_db_connection():
    """
    Close database connection and cleanup resources.
    Call this when shutting down the application.
    """
    try:
        ScopedSession.remove()
        engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")


# Event listener to log slow queries (optional, for debugging)
@event.listens_for(engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log SQL queries for debugging (optional)."""
    conn.info.setdefault('query_start_time', []).append(os.times())


@event.listens_for(engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log slow queries for debugging (optional)."""
    total = os.times()[4] - conn.info['query_start_time'].pop()[4]
    if total > 1.0:  # Log queries taking more than 1 second
        logger.warning(f"Slow query detected ({total:.2f}s): {statement[:100]}...")


# Export commonly used items
__all__ = [
    'engine',
    'SessionLocal',
    'ScopedSession',
    'get_db',
    'get_db_session',
    'test_connection',
    'get_database_info',
    'close_db_connection',
    'retry_on_db_error'
]