# Deployment and Operations Guide

## Overview

This guide covers deployment, database management, CI/CD, and operational procedures for Local Newsifier.

## Table of Contents
- [Deployment](#deployment)
- [Database Management](#database-management)
- [CI/CD Pipeline](#cicd-pipeline)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## Deployment

### Railway Deployment

Local Newsifier is designed for deployment on Railway with a single web process architecture.

#### Configuration

```toml
# railway.toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "uvicorn src.local_newsifier.api.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 30
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

#### Environment Variables

Required environment variables for Railway:

```bash
# Database (provided by Railway)
DATABASE_URL=postgresql://user:pass@host:5432/railway

# PostgreSQL Components (auto-populated by Railway)
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_HOST
POSTGRES_PORT
POSTGRES_DB

# Application
APIFY_TOKEN=your_apify_token
APIFY_WEBHOOK_SECRET=optional_webhook_secret

# Optional
LOG_LEVEL=INFO
```

#### Single Process Architecture

- **Web Process**: Handles API, webhooks, and background tasks
- **No Workers**: FastAPI BackgroundTasks handle async processing
- **No Scheduler**: Use Railway cron jobs or external schedulers
- **No Redis**: Unless needed for caching (not for Celery)

### Local Development

#### Database Initialization

For Cursor-specific development databases:

```bash
# Install dependencies
poetry install

# Initialize database
poetry run python scripts/init_cursor_db.py

# Source environment
source .env.cursor
```

This creates a unique database named `local_newsifier_<cursor_id>`.

#### Running Locally

```bash
# Start API server
make run-api
# or
uvicorn src.local_newsifier.api.main:app --reload

# Run with specific port
uvicorn src.local_newsifier.api.main:app --reload --port 8001
```

## Database Management

### Database Schema

The application uses SQLModel with PostgreSQL. Key tables include:
- `articles`: News articles
- `entities`: Extracted entities
- `canonical_entities`: Resolved entity references
- `analysis_results`: Sentiment and trend analysis
- `rss_feeds`: RSS feed configurations
- `apify_webhook_raw`: Apify webhook payloads
- `apify_source_configs`: Apify actor configurations

### Migrations

Using Alembic for database migrations:

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one revision
alembic downgrade -1
```

### Database Diagnostics

#### Statistics
```bash
# Show database statistics
nf db stats

# Output as JSON
nf db stats --json
```

#### Finding Duplicates
```bash
# Show duplicate articles
nf db duplicates

# Show more duplicates
nf db duplicates --limit 20

# Purge duplicates (keeps oldest)
nf db purge-duplicates --yes
```

#### Listing Articles
```bash
# List recent articles
nf db articles --limit 10

# Filter by date
nf db articles --days 7

# Filter by source
nf db articles --source apify

# Filter by status
nf db articles --status published
```

#### Inspecting Records
```bash
# Inspect specific record
nf db inspect articles 123

# Show related data
nf db inspect articles 123 --related
```

### Database Reset

```bash
# Complete reset (WARNING: Deletes all data)
poetry run python scripts/reset_db.py --confirm
```

## CI/CD Pipeline

### GitHub Actions

The project uses GitHub Actions for continuous integration.

#### Test Workflow

```yaml
name: Tests
on:
  push:
    branches: [main]
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install Poetry
        run: pipx install poetry
      - name: Install dependencies
        run: poetry install
      - name: Run tests
        run: poetry run pytest tests/ -v
```

#### PR Chain Support

The CI supports testing PRs that target other PRs:
- Uses `pull_request_target` event with security checks
- Ensures PR code is checked out and tested
- Provides same feedback as PRs targeting main

### Deployment Pipeline

Railway automatically deploys on push to main:

1. **Build**: Nixpacks detects Python project
2. **Install**: Dependencies from `pyproject.toml`
3. **Migrate**: Run Alembic migrations (if configured)
4. **Start**: Launch Uvicorn server

## Monitoring

### Health Checks

```bash
# Check API health
curl https://your-app.railway.app/health

# Response
{
  "status": "healthy",
  "database": "connected",
  "version": "1.0.0"
}
```

### Logging

The application uses structured logging:

```python
import logging
logger = logging.getLogger(__name__)

# Log levels
logger.debug("Detailed information")
logger.info("General information")
logger.warning("Warning messages")
logger.error("Error messages")
```

### Key Metrics to Monitor

1. **API Performance**
   - Response times
   - Error rates
   - Request volume

2. **Database**
   - Connection pool usage
   - Query performance
   - Table sizes

3. **External Integrations**
   - Apify API calls
   - RSS feed fetch times
   - Webhook delivery rates

## Troubleshooting

### Common Issues

#### Database Connection Errors
```bash
# Check connection
psql $DATABASE_URL -c "SELECT 1"

# Check Railway logs
railway logs
```

#### Webhook Not Processing
```bash
# Check webhook was received
nf db inspect apify_webhook_raw --limit 10

# Check for errors in logs
railway logs | grep "webhook"
```

#### Memory Issues
- Check for large query results
- Monitor connection pool size
- Review background task queuing

### Debug Mode

Enable debug logging:

```bash
# Set in environment
LOG_LEVEL=DEBUG

# Or in code
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Profiling

```bash
# Profile specific endpoint
python -m cProfile -o profile.out src/local_newsifier/api/main.py

# Analyze profile
python -m pstats profile.out
```

## Backup and Recovery

### Database Backup

```bash
# Manual backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Restore from backup
psql $DATABASE_URL < backup_20240125.sql
```

### Railway Backups

Railway provides automatic daily backups for databases. Access via Railway dashboard.

## Security Considerations

1. **Environment Variables**
   - Never commit secrets to git
   - Use Railway's secret management
   - Rotate tokens regularly

2. **API Security**
   - Validate all inputs
   - Use webhook secrets
   - Implement rate limiting (if needed)

3. **Database Security**
   - Use connection pooling
   - Parameterized queries (via ORM)
   - Regular security updates

## Scaling Considerations

### Horizontal Scaling

Railway supports horizontal scaling:
```bash
# Scale to 3 instances
railway scale web=3
```

### Performance Optimization

1. **Database Indexes**
   - Add indexes for common queries
   - Monitor slow queries
   - Use EXPLAIN ANALYZE

2. **Caching**
   - Cache expensive computations
   - Use Redis if needed
   - Cache API responses

3. **Background Tasks**
   - Use FastAPI BackgroundTasks
   - Queue long-running tasks
   - Monitor task completion

## Maintenance Tasks

### Regular Maintenance

```bash
# Weekly: Clean old webhook data
nf db cleanup-webhooks --days 30

# Monthly: Analyze database
psql $DATABASE_URL -c "ANALYZE;"

# Quarterly: Review and archive old data
nf db archive-articles --before 2024-01-01
```

### Updates and Patches

```bash
# Update dependencies
poetry update

# Check for security updates
poetry audit

# Update Railway runtime
# (Automatic via Nixpacks)
```
