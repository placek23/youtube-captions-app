"""
Database migration script for YouTube Channel Subscription System.

This script creates all database tables defined in models.py.
Safe to run multiple times - uses CREATE IF NOT EXISTS pattern.

Usage:
    python migrate_db.py
"""

import sys
import logging
from sqlalchemy import inspect, text
from database import engine, test_connection, get_database_info
from models import Base, Channel, Video, ProcessingStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_table_exists(table_name):
    """
    Check if a table exists in the database.

    Args:
        table_name: Name of the table to check.

    Returns:
        bool: True if table exists, False otherwise.
    """
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def get_existing_tables():
    """
    Get list of existing tables in the database.

    Returns:
        list: List of table names.
    """
    inspector = inspect(engine)
    return inspector.get_table_names()


def create_tables():
    """
    Create all tables defined in models.

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        logger.info("Creating database tables...")

        # Get existing tables before creation
        existing_before = set(get_existing_tables())
        logger.info(f"Existing tables before migration: {existing_before or 'None'}")

        # Create all tables defined in Base metadata
        Base.metadata.create_all(bind=engine)

        # Get tables after creation
        existing_after = set(get_existing_tables())
        new_tables = existing_after - existing_before

        if new_tables:
            logger.info(f"✓ Successfully created new tables: {new_tables}")
        else:
            logger.info("✓ All tables already exist, no new tables created")

        # Verify expected tables exist
        expected_tables = {'channels', 'videos'}
        missing_tables = expected_tables - existing_after

        if missing_tables:
            logger.error(f"✗ Missing expected tables: {missing_tables}")
            return False

        logger.info(f"✓ All expected tables exist: {expected_tables}")
        return True

    except Exception as e:
        logger.error(f"✗ Failed to create tables: {e}")
        return False


def verify_tables():
    """
    Verify table structure and indexes.

    Returns:
        bool: True if all tables are correctly structured.
    """
    try:
        logger.info("\nVerifying table structure...")
        inspector = inspect(engine)

        # Verify Channel table
        if check_table_exists('channels'):
            columns = [col['name'] for col in inspector.get_columns('channels')]
            indexes = [idx['name'] for idx in inspector.get_indexes('channels')]
            logger.info(f"  channels table columns: {columns}")
            logger.info(f"  channels table indexes: {indexes}")

            required_columns = ['id', 'channel_id', 'channel_name', 'channel_url', 'created_at']
            missing_columns = set(required_columns) - set(columns)
            if missing_columns:
                logger.error(f"✗ Missing columns in channels table: {missing_columns}")
                return False
        else:
            logger.error("✗ channels table does not exist")
            return False

        # Verify Video table
        if check_table_exists('videos'):
            columns = [col['name'] for col in inspector.get_columns('videos')]
            indexes = [idx['name'] for idx in inspector.get_indexes('videos')]
            logger.info(f"  videos table columns: {columns}")
            logger.info(f"  videos table indexes: {indexes}")

            required_columns = ['id', 'channel_id', 'video_id', 'title', 'processing_status', 'created_at']
            missing_columns = set(required_columns) - set(columns)
            if missing_columns:
                logger.error(f"✗ Missing columns in videos table: {missing_columns}")
                return False
        else:
            logger.error("✗ videos table does not exist")
            return False

        logger.info("✓ Table structure verification passed")
        return True

    except Exception as e:
        logger.error(f"✗ Table verification failed: {e}")
        return False


def get_table_counts():
    """
    Get row counts for all tables.

    Returns:
        dict: Dictionary with table names and row counts.
    """
    try:
        counts = {}
        with engine.connect() as connection:
            if check_table_exists('channels'):
                result = connection.execute(text("SELECT COUNT(*) FROM channels"))
                counts['channels'] = result.scalar()

            if check_table_exists('videos'):
                result = connection.execute(text("SELECT COUNT(*) FROM videos"))
                counts['videos'] = result.scalar()

        return counts
    except Exception as e:
        logger.error(f"Failed to get table counts: {e}")
        return {}


def main():
    """
    Main migration function.
    """
    print("=" * 70)
    print("YouTube Channel Subscription System - Database Migration")
    print("=" * 70)
    print()

    # Step 1: Test database connection
    logger.info("Step 1: Testing database connection...")
    if not test_connection():
        logger.error("✗ Database connection failed. Please check your DATABASE_URL.")
        logger.error("  Make sure you have set the correct Vercel Postgres credentials in your .env file.")
        sys.exit(1)

    # Show database info
    db_info = get_database_info()
    if db_info:
        print()
        print("Database Information:")
        print(f"  Database: {db_info['database']}")
        print(f"  User: {db_info['user']}")
        print(f"  Host: {db_info['url']}")
        print()

    # Step 2: Create tables
    logger.info("Step 2: Creating database tables...")
    if not create_tables():
        logger.error("✗ Table creation failed")
        sys.exit(1)

    # Step 3: Verify tables
    logger.info("Step 3: Verifying table structure...")
    if not verify_tables():
        logger.error("✗ Table verification failed")
        sys.exit(1)

    # Step 4: Show table counts
    print()
    logger.info("Step 4: Checking table row counts...")
    counts = get_table_counts()
    if counts:
        for table, count in counts.items():
            logger.info(f"  {table}: {count} rows")

    # Success!
    print()
    print("=" * 70)
    print("✓ Database migration completed successfully!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Add your YouTube API key to .env (YOUTUBE_API_KEY)")
    print("  2. Start the Flask application: python app.py")
    print("  3. Login and start adding YouTube channels")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n✗ Migration failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)