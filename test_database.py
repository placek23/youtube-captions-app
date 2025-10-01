#!/usr/bin/env python3
"""
Database Connection Test Script
Tests connection to Vercel Postgres and verifies all tables exist
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

def test_database_connection():
    """Test database connection and table structure"""
    print("=" * 60)
    print("DATABASE CONNECTION TEST")
    print("=" * 60)

    # Check environment variables
    print("\n1. Checking environment variables...")
    postgres_url = os.getenv('POSTGRES_URL')
    database_url = os.getenv('DATABASE_URL')
    prisma_url = os.getenv('POSTGRES_PRISMA_URL')

    print(f"   POSTGRES_URL: {'[OK] Set' if postgres_url else '[X] Not set'}")
    print(f"   DATABASE_URL: {'[OK] Set' if database_url else '[X] Not set'}")
    print(f"   POSTGRES_PRISMA_URL: {'[OK] Set' if prisma_url else '[X] Not set'}")

    if not any([postgres_url, database_url, prisma_url]):
        print("\n[X] ERROR: No database URL found in environment variables")
        return False

    # Import database module
    print("\n2. Importing database module...")
    try:
        from database import get_db, engine
        print("   [OK] Database module imported successfully")
    except Exception as e:
        print(f"   [X] ERROR: Failed to import database module: {e}")
        return False

    # Test connection
    print("\n3. Testing database connection...")
    try:
        from sqlalchemy import text
        db = next(get_db())
        print("   [OK] Successfully connected to database")

        # Test query
        result = db.execute(text("SELECT 1 as test")).fetchone()
        if result[0] == 1:
            print("   [OK] Test query executed successfully")

        db.close()
    except Exception as e:
        print(f"   [X] ERROR: Database connection failed: {e}")
        return False

    # Check tables
    print("\n4. Verifying database tables...")
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        expected_tables = ['channels', 'videos']
        for table in expected_tables:
            if table in tables:
                print(f"   [OK] Table '{table}' exists")

                # Show columns
                columns = inspector.get_columns(table)
                print(f"      Columns: {', '.join([col['name'] for col in columns])}")
            else:
                print(f"   [X] Table '{table}' NOT found")

        # Show all tables
        print(f"\n   Total tables found: {len(tables)}")
        if tables:
            print(f"   Tables: {', '.join(tables)}")

    except Exception as e:
        print(f"   [X] ERROR: Failed to verify tables: {e}")
        return False

    # Test models
    print("\n5. Testing SQLAlchemy models...")
    try:
        from models import Channel, Video
        db = next(get_db())

        # Count channels
        channel_count = db.query(Channel).count()
        print(f"   [OK] Channel model working - {channel_count} channels in database")

        # Count videos
        video_count = db.query(Video).count()
        print(f"   [OK] Video model working - {video_count} videos in database")

        db.close()
    except Exception as e:
        print(f"   [X] ERROR: Model test failed: {e}")
        return False

    print("\n" + "=" * 60)
    print("[OK] ALL DATABASE TESTS PASSED")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_database_connection()
    sys.exit(0 if success else 1)
