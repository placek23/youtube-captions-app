# Database Migrations Guide

This document explains how to initialize, migrate, and manage the PostgreSQL database for the YouTube Channel Subscription & AI Summary Manager application.

## Table of Contents
- [Database Overview](#database-overview)
- [Initial Setup](#initial-setup)
- [Running Migrations](#running-migrations)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Rollback Strategy](#rollback-strategy)
- [Schema Changes](#schema-changes)

## Database Overview

The application uses PostgreSQL with SQLAlchemy ORM. The database consists of two main tables:

### Channels Table
Stores subscribed YouTube channels.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Serial | PRIMARY KEY | Auto-incrementing ID |
| channel_id | VARCHAR(100) | UNIQUE, NOT NULL | YouTube channel ID |
| channel_name | VARCHAR(255) | NOT NULL | Channel display name |
| channel_url | VARCHAR(500) | NOT NULL | Full YouTube URL |
| thumbnail_url | VARCHAR(500) | | Channel thumbnail URL |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Creation timestamp |

**Indexes:**
- `ix_channels_channel_id` on `channel_id` (unique)

### Videos Table
Stores videos from subscribed channels with processing status.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Serial | PRIMARY KEY | Auto-incrementing ID |
| channel_id | Integer | FOREIGN KEY(channels.id) ON DELETE CASCADE | Reference to channel |
| video_id | VARCHAR(20) | UNIQUE, NOT NULL | YouTube video ID |
| title | VARCHAR(500) | NOT NULL | Video title |
| thumbnail_url | VARCHAR(500) | | Video thumbnail URL |
| published_at | TIMESTAMP | NOT NULL | YouTube publish date |
| caption_text | TEXT | | Extracted captions |
| short_summary | TEXT | | 50-100 word summary |
| detailed_summary | TEXT | | Comprehensive summary |
| processing_status | VARCHAR(20) | NOT NULL, DEFAULT 'pending' | pending/processing/completed/failed |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last update timestamp |

**Indexes:**
- `ix_videos_video_id` on `video_id` (unique)
- `ix_videos_channel_id` on `channel_id`
- `ix_videos_published_at` on `published_at`
- `ix_videos_processing_status` on `processing_status`

**Foreign Keys:**
- `channel_id` references `channels(id)` with `ON DELETE CASCADE`

## Initial Setup

### Prerequisites
1. PostgreSQL database instance (local or Vercel Postgres)
2. Database connection URL in `.env` file
3. Python dependencies installed

### Environment Configuration

Create a `.env` file with database credentials:

```env
# For Vercel Postgres (recommended)
POSTGRES_PRISMA_URL=postgresql://user:password@host:port/database?sslmode=require&pgbouncer=true
POSTGRES_URL=postgresql://user:password@host:port/database?sslmode=require

# OR for local/other PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/youtube_captions
```

**Connection Priority:**
1. `POSTGRES_PRISMA_URL` (pgBouncer pooling - best for Vercel)
2. `DATABASE_URL` (standard connection)
3. `POSTGRES_URL` (alternative)

## Running Migrations

### First-Time Database Initialization

1. **Verify database connection:**
   ```bash
   python test_database.py
   ```

   This will check:
   - Environment variables are set
   - Database is reachable
   - Connection is valid

2. **Run migrations:**
   ```bash
   python migrate_db.py
   ```

   This script will:
   - Create all tables if they don't exist
   - Add indexes and constraints
   - Handle "already exists" errors gracefully
   - Verify table creation

### Expected Output

```
============================================================
DATABASE MIGRATION SCRIPT
============================================================

Environment Variables:
   POSTGRES_PRISMA_URL: [OK] Set

Database Connection:
   [OK] Successfully connected to database

Creating Tables:
   [OK] Table 'channels' created successfully
   [OK] Table 'videos' created successfully

Verification:
   [OK] All tables verified
   [OK] channels table exists with 6 columns
   [OK] videos table exists with 12 columns

============================================================
[OK] MIGRATION COMPLETED SUCCESSFULLY
============================================================
```

## Verification

### Manual Verification

After running migrations, verify the database schema:

1. **Using test script:**
   ```bash
   python test_database.py
   ```

2. **Using psql (if you have it installed):**
   ```bash
   # Get connection string from .env
   psql $POSTGRES_URL

   # List tables
   \dt

   # Describe tables
   \d channels
   \d videos

   # Check indexes
   \di

   # Exit
   \q
   ```

3. **Using database GUI:**
   - Use TablePlus, DBeaver, or pgAdmin
   - Connect using database URL from `.env`
   - Verify tables, columns, and indexes

### Automated Verification

The `test_database.py` script performs comprehensive checks:
- Environment variable validation
- Database connectivity
- Table existence
- Column verification
- Model functionality
- Data counts

Run it anytime to verify database health:
```bash
python test_database.py
```

## Troubleshooting

### Connection Errors

**Error**: `could not connect to server`
- **Cause**: Database not accessible or wrong URL
- **Solution**:
  - Verify database URL in `.env`
  - Check database is running
  - For Vercel: Ensure database is provisioned

**Error**: `FATAL: password authentication failed`
- **Cause**: Incorrect credentials
- **Solution**: Verify username/password in connection string

**Error**: `SSL connection required`
- **Cause**: Missing `sslmode=require` in connection string
- **Solution**: Add `?sslmode=require` to connection URL

### Migration Errors

**Error**: `relation "channels" already exists`
- **Cause**: Tables already created
- **Solution**: This is normal - script handles it gracefully

**Error**: `could not create unique index`
- **Cause**: Duplicate data in columns with unique constraint
- **Solution**:
  - Check for duplicate `channel_id` or `video_id`
  - Remove duplicates before creating index

**Error**: `permission denied for schema public`
- **Cause**: Insufficient database privileges
- **Solution**: Ensure database user has CREATE TABLE permissions

### Connection Pool Issues (Vercel)

**Error**: `remaining connection slots are reserved`
- **Cause**: Too many connections (Vercel limit)
- **Solution**:
  - Use `POSTGRES_PRISMA_URL` (pgBouncer pooling)
  - Verify NullPool is configured in `database.py`
  - Check for connection leaks

## Rollback Strategy

### Manual Rollback

If you need to rollback the database:

1. **Drop all tables:**
   ```sql
   DROP TABLE IF EXISTS videos CASCADE;
   DROP TABLE IF EXISTS channels CASCADE;
   ```

2. **Re-run migrations:**
   ```bash
   python migrate_db.py
   ```

### Backup Before Migration

For production environments:

1. **Backup database:**
   ```bash
   # For local PostgreSQL
   pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

   # For Vercel - use Vercel dashboard or CLI
   vercel env pull
   ```

2. **Restore from backup if needed:**
   ```bash
   psql $DATABASE_URL < backup_20251001_120000.sql
   ```

## Schema Changes

### Adding New Columns

When adding new columns to existing tables:

1. **Update `models.py`** with new column definitions
2. **Create migration script** (example):

   ```python
   # add_column_migration.py
   from sqlalchemy import text
   from database import engine, get_db

   def add_language_column():
       """Add language column to videos table"""
       with engine.connect() as conn:
           try:
               conn.execute(text("""
                   ALTER TABLE videos
                   ADD COLUMN IF NOT EXISTS language VARCHAR(10)
               """))
               conn.commit()
               print("[OK] Added language column")
           except Exception as e:
               print(f"[X] Error: {e}")

   if __name__ == "__main__":
       add_language_column()
   ```

3. **Run migration:**
   ```bash
   python add_column_migration.py
   ```

### Adding New Tables

1. **Define model** in `models.py`
2. **Run standard migration:**
   ```bash
   python migrate_db.py
   ```
   - Script automatically creates new tables
   - Leaves existing tables untouched

### Modifying Constraints

For constraint changes (e.g., changing column type, adding indexes):

1. **Create specific migration script**
2. **Test on local/dev database first**
3. **Backup production before applying**

Example:
```python
# modify_constraint.py
from sqlalchemy import text
from database import engine

def add_index_on_column():
    """Add index to improve query performance"""
    with engine.connect() as conn:
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_videos_language
                ON videos(language)
            """))
            conn.commit()
            print("[OK] Index created")
        except Exception as e:
            print(f"[X] Error: {e}")

if __name__ == "__main__":
    add_index_on_column()
```

## Best Practices

### Development Environment

1. **Always test migrations locally first**
2. **Use separate development database**
3. **Run verification after each migration**
4. **Keep migration scripts in version control**

### Production Environment

1. **Backup before migrations**
2. **Test migrations in staging environment**
3. **Plan for rollback if needed**
4. **Monitor database performance after changes**
5. **Document all schema changes**

### Vercel-Specific

1. **Use POSTGRES_PRISMA_URL for connection pooling**
2. **Be aware of connection limits (100 on Vercel Hobby)**
3. **Use Vercel dashboard for database management**
4. **Monitor cold start times after schema changes**

## Migration Checklist

Before running migrations in production:

- [ ] Backup current database
- [ ] Test migration on local database
- [ ] Test migration on staging database
- [ ] Verify application works with new schema
- [ ] Document changes in this file
- [ ] Plan rollback procedure
- [ ] Schedule migration during low-traffic period
- [ ] Run migration
- [ ] Verify tables and indexes created
- [ ] Run test suite
- [ ] Monitor application logs
- [ ] Test critical user workflows

## Support

For migration issues:
- Check application logs in terminal or Vercel dashboard
- Run `python test_database.py` for diagnostics
- Review this document for troubleshooting steps
- Check PostgreSQL logs if accessible

---

**Last Updated**: 2025-10-01
**Schema Version**: 1.0.0
**Compatible with**: Phase 9+ of channel_subscriptions_plan.md
