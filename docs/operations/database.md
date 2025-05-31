# Database Guide

## Overview

Local Newsifier uses PostgreSQL with SQLModel ORM for data persistence. This guide covers database setup, management, and best practices.

## Table of Contents
- [Setup](#setup)
- [Schema Overview](#schema-overview)
- [Development Databases](#development-databases)
- [CLI Commands](#cli-commands)
- [Migrations](#migrations)
- [Best Practices](#best-practices)

## Setup

### Production Database

Railway provides PostgreSQL databases with automatic connection string configuration:

```bash
# Automatically set by Railway
DATABASE_URL=postgresql://user:pass@host:5432/railway
```

### Local Development

For local development, you can use:
1. Local PostgreSQL installation
2. Docker PostgreSQL container
3. Railway development database

```bash
# Docker PostgreSQL
docker run -d \
  --name local-newsifier-db \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=local_newsifier \
  -p 5432:5432 \
  postgres:15

# Set environment variable
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/local_newsifier
```

## Schema Overview

### Core Tables

#### Articles
```sql
CREATE TABLE articles (
    id SERIAL PRIMARY KEY,
    url VARCHAR UNIQUE NOT NULL,
    title VARCHAR NOT NULL,
    content TEXT NOT NULL,
    source VARCHAR DEFAULT 'unknown',
    published_at TIMESTAMP,
    status VARCHAR DEFAULT 'published',
    scraped_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Entities
```sql
CREATE TABLE entities (
    id SERIAL PRIMARY KEY,
    article_id INTEGER REFERENCES articles(id),
    text VARCHAR NOT NULL,
    type VARCHAR NOT NULL,
    canonical_entity_id INTEGER REFERENCES canonical_entities(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### RSS Feeds
```sql
CREATE TABLE rss_feeds (
    id SERIAL PRIMARY KEY,
    url VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_fetched_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Apify Integration
```sql
CREATE TABLE apify_webhook_raw (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR UNIQUE NOT NULL,
    actor_id VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE apify_source_configs (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    actor_id VARCHAR NOT NULL,
    run_input JSONB NOT NULL,
    schedule_id VARCHAR,
    webhook_url VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Development Databases

### Cursor-Specific Databases

To avoid conflicts between different Cursor instances, each development environment gets its own database:

```bash
# Initialize Cursor-specific database
poetry run python scripts/init_cursor_db.py

# This creates:
# - Database: local_newsifier_<cursor_id>
# - Environment file: .env.cursor
# - All required tables

# Use the database
source .env.cursor
```

### Database Reset

```bash
# Complete reset (WARNING: Deletes all data)
poetry run python scripts/reset_db.py --confirm

# Reset specific tables
poetry run python scripts/reset_db.py --tables articles entities
```

## CLI Commands

### Database Statistics

```bash
# Show overall statistics
nf db stats

# Output format options
nf db stats --json
nf db stats --yaml
```

Shows:
- Total articles and date range
- RSS feed counts (active/inactive)
- Entity statistics
- Processing logs

### Finding Duplicates

```bash
# Find duplicate articles
nf db duplicates

# Show more results
nf db duplicates --limit 50

# Purge duplicates (keeps oldest)
nf db purge-duplicates --yes
```

### Article Management

```bash
# List recent articles
nf db articles --limit 20

# Filter by date
nf db articles --days 7
nf db articles --since "2024-01-01"

# Filter by source
nf db articles --source rss
nf db articles --source apify

# Filter by status
nf db articles --status published
nf db articles --status draft

# Combine filters
nf db articles --source apify --days 7 --limit 50
```

### Record Inspection

```bash
# Inspect specific record
nf db inspect articles 123

# Show with related data
nf db inspect articles 123 --related

# Inspect other tables
nf db inspect entities 456
nf db inspect rss_feeds 789
nf db inspect apify_webhook_raw 101
```

### Feed Management

```bash
# List all feeds
nf feeds list

# Add new feed
nf feeds add https://example.com/rss.xml --name "Example News"

# Update feed
nf feeds update 123 --active false

# Process specific feed
nf feeds process 123
```

## Migrations

### Using Alembic

```bash
# Check current version
alembic current

# Create new migration
alembic revision --autogenerate -m "Add new column to articles"

# Apply migrations
alembic upgrade head

# Rollback one version
alembic downgrade -1

# Show migration history
alembic history
```

### Manual Schema Updates

For development/testing:

```python
from sqlmodel import SQLModel
from local_newsifier.database.engine import engine

# Create all tables
SQLModel.metadata.create_all(engine)

# Drop and recreate
SQLModel.metadata.drop_all(engine)
SQLModel.metadata.create_all(engine)
```

## Best Practices

### Connection Management

1. **Use Session Context Managers**
```python
from local_newsifier.database.engine import get_session

def process_articles():
    with get_session() as session:
        articles = session.query(Article).all()
        # Process articles
        session.commit()
```

2. **Avoid Long-Running Sessions**
- Keep sessions short-lived
- Use session per request in API
- Close sessions promptly

### Query Optimization

1. **Use Indexes**
```sql
-- Add indexes for common queries
CREATE INDEX idx_articles_source ON articles(source);
CREATE INDEX idx_articles_created_at ON articles(created_at);
CREATE INDEX idx_entities_type ON entities(type);
```

2. **Batch Operations**
```python
# Good - batch insert
session.add_all([article1, article2, article3])
session.commit()

# Bad - individual inserts
for article in articles:
    session.add(article)
    session.commit()
```

3. **Eager Loading**
```python
# Load related data in one query
articles = session.query(Article)\
    .options(selectinload(Article.entities))\
    .all()
```

### Data Integrity

1. **Use Constraints**
- Unique constraints on URLs
- Foreign key relationships
- NOT NULL where appropriate

2. **Validate Before Insert**
```python
# Use Pydantic models for validation
article_data = ArticleCreate(**data)
article = Article(**article_data.model_dump())
```

3. **Handle Duplicates**
```python
existing = session.query(Article).filter_by(url=url).first()
if existing:
    logger.info(f"Article already exists: {url}")
    return existing
```

### Maintenance

1. **Regular Cleanup**
```bash
# Remove old webhook data
DELETE FROM apify_webhook_raw
WHERE created_at < NOW() - INTERVAL '30 days';

# Vacuum to reclaim space
VACUUM ANALYZE;
```

2. **Monitor Growth**
```sql
-- Check table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

3. **Backup Strategy**
- Railway: Automatic daily backups
- Local: Regular pg_dump backups
- Test restore procedures

## Troubleshooting

### Common Issues

1. **Connection Refused**
```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Check connection string
psql $DATABASE_URL -c "SELECT 1"
```

2. **Permission Denied**
```sql
-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE local_newsifier TO myuser;
GRANT ALL ON ALL TABLES IN SCHEMA public TO myuser;
```

3. **Slow Queries**
```sql
-- Enable query logging
SET log_statement = 'all';
SET log_duration = on;

-- Find slow queries
SELECT query, mean_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

### Debug Commands

```bash
# Show active connections
psql $DATABASE_URL -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"

# Kill stuck query
psql $DATABASE_URL -c "SELECT pg_cancel_backend(pid) FROM pg_stat_activity WHERE query_start < NOW() - INTERVAL '10 minutes';"

# Analyze query plan
psql $DATABASE_URL -c "EXPLAIN ANALYZE SELECT * FROM articles WHERE source = 'apify';"
```
