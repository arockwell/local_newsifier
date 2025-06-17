# Alembic Deployment Issues Analysis

## Overview

Your server deployment is experiencing Alembic-related issues that can prevent proper database initialization and migration management. This analysis identifies the current issues and provides solutions.

## Current Issues

### 1. Migration History Chain
Looking at your migration files, the current migration chain is:
```
d3d111e9579d (initial_schema)
    ↓
d6d7f6c7b282 (add_rss_feed_models)
    ↓
a6b9cd123456 (add_apify_models)
    ↓
a8c61d1f7283 (add_apify_webhook_raw_table)
    ↓
1a51ab641644 (fix_apify_webhook_unique_constraint)
    ↓
13e391b8dbdc (add_schedule_id_to_apify_config)
    ↓
dbc1bc75a79e (rename_tables_to_plural)
    ↓
e8f921b5c3d1 (make_article_title_optional) <- HEAD
```

### 2. Deployment Process Issues

Your deployment process (from `railway.json` and `Procfile`) runs:
```bash
bash scripts/init_spacy_models.sh &&
bash scripts/init_alembic.sh &&
alembic upgrade head &&
python -m uvicorn local_newsifier.api.main:app --host 0.0.0.0 --port $PORT
```

The `init_alembic.sh` script has logic that can cause issues:
- It checks if tables exist in the database
- If tables exist but Alembic hasn't tracked them, it runs `alembic stamp head`
- If tables don't exist, it runs `alembic upgrade head`

### 3. Common Deployment Problems

#### A. Fresh Database vs Existing Database Confusion
When deploying to a new environment:
- If the database already has tables (from a previous deployment or manual creation), Alembic doesn't know which migration created them
- Running `alembic stamp head` marks all migrations as applied without actually running them
- This can lead to schema mismatches if the existing tables don't match the latest migration

#### B. Migration State Mismatch
- The `alembic_version` table tracks which migrations have been applied
- If this gets out of sync with actual database schema, you'll have problems
- Common causes: manual table modifications, failed partial migrations, database restores

#### C. Concurrent Migration Attempts
- If multiple instances start simultaneously (common in cloud deployments), they might try to run migrations concurrently
- This can cause lock conflicts or partial migrations

## Solutions

### 1. Immediate Fix for Current Deployment

If your deployment is failing, try these steps:

#### Option A: Clean Start (if data loss is acceptable)
```bash
# Drop all tables and start fresh
alembic downgrade base
alembic upgrade head
```

#### Option B: Force Sync (if you need to preserve data)
```bash
# Check current state
alembic current

# If no version is set but tables exist, stamp with the correct version
# First, verify your schema matches a specific migration
alembic stamp e8f921b5c3d1  # Use the latest migration ID

# Then run any pending migrations
alembic upgrade head
```

### 2. Improved Deployment Script

Create a more robust `init_alembic.sh`:

```bash
#!/bin/bash
set -e

echo "Starting database initialization..."

# Function to check if alembic_version table exists
check_alembic_table() {
    python -c "
from sqlalchemy import inspect, create_engine
from local_newsifier.config.settings import get_settings
settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
inspector = inspect(engine)
tables = inspector.get_table_names()
print('exists' if 'alembic_version' in tables else 'not_exists')
"
}

# Function to get current revision
get_current_revision() {
    alembic current 2>/dev/null | grep -oE '[a-f0-9]{12}' | head -1 || echo "none"
}

ALEMBIC_TABLE=$(check_alembic_table)
CURRENT_REV=$(get_current_revision)

echo "Alembic table status: $ALEMBIC_TABLE"
echo "Current revision: $CURRENT_REV"

if [[ $ALEMBIC_TABLE == "not_exists" ]]; then
    echo "No alembic_version table found. Running all migrations..."
    alembic upgrade head
elif [[ $CURRENT_REV == "none" ]]; then
    echo "Alembic table exists but no revision set. Checking schema..."
    # This is a dangerous state - requires manual intervention
    echo "WARNING: Database is in inconsistent state. Manual intervention required."
    echo "Please verify schema and run: alembic stamp <appropriate-revision>"
    exit 1
else
    echo "Running pending migrations from $CURRENT_REV..."
    alembic upgrade head
fi

echo "Database initialization complete!"
```

### 3. Best Practices for Alembic in Production

#### A. Single Migration Runner
Ensure only one instance runs migrations:
```python
# In your startup code
import fcntl
import os

def run_migrations():
    lock_file = '/tmp/alembic.lock'
    with open(lock_file, 'w') as f:
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            # Run migrations here
            os.system('alembic upgrade head')
        except IOError:
            print("Another instance is running migrations")
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)
```

#### B. Health Check Considerations
- Don't include migration status in health checks
- Let migrations complete before starting the web server
- Consider a separate migration job/container

#### C. Migration Testing
Before deploying:
```bash
# Test migration up
alembic upgrade head

# Test migration down
alembic downgrade -1

# Test migration up again
alembic upgrade head
```

### 4. Debugging Current Issues

To diagnose your current deployment:

```bash
# 1. Check database connection
python -c "
from local_newsifier.config.settings import get_settings
from sqlalchemy import create_engine
settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
print('Connected successfully')
"

# 2. Check current migration state
alembic current

# 3. Check actual tables in database
python -c "
from sqlalchemy import inspect, create_engine
from local_newsifier.config.settings import get_settings
settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
inspector = inspect(engine)
tables = sorted(inspector.get_table_names())
print('Tables in database:')
for table in tables:
    print(f'  - {table}')
"

# 4. Check for pending migrations
alembic history --verbose
```

### 5. Railway-Specific Considerations

For Railway deployments:
1. Use the `railway run` command to execute migrations in the correct environment
2. Consider using a release phase for migrations instead of running them at startup
3. Ensure `DATABASE_URL` is properly set in Railway environment variables
4. Monitor deployment logs for migration errors

### 6. Recovery Procedures

If your deployment is stuck:

#### A. Schema Mismatch
```bash
# Generate SQL for current state
alembic upgrade head --sql > desired_schema.sql

# Compare with actual schema
pg_dump -s $DATABASE_URL > actual_schema.sql

# Manually apply differences or reset
```

#### B. Corrupted Migration State
```bash
# Last resort - manually set version
psql $DATABASE_URL -c "DELETE FROM alembic_version;"
psql $DATABASE_URL -c "INSERT INTO alembic_version (version_num) VALUES ('e8f921b5c3d1');"
```

## Recommendations

1. **Separate Migration Phase**: Run migrations as a separate deployment step, not at application startup
2. **Idempotent Migrations**: Ensure migrations can be run multiple times safely
3. **Monitoring**: Add logging and alerts for migration failures
4. **Backup Strategy**: Always backup before running migrations in production
5. **Staging Environment**: Test migrations in a staging environment first

## Next Steps

1. Check your current deployment logs for specific Alembic errors
2. Verify your database connection and credentials
3. Run the debugging commands above to understand current state
4. Apply the appropriate fix based on your situation
5. Update your deployment scripts to be more robust

Remember: Alembic migrations should be treated as critical operations that can break your application if not handled properly. Always have a rollback plan.
