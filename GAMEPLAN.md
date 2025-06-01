# Production Database Migration Status Investigation

## Goal
Determine if the production database is on the latest Alembic migration version and identify any discrepancies.

## Steps

### 1. Check Latest Migration in Repository
```bash
# List all migration files to find the latest one
ls -la alembic/versions/ | grep -E '\.py$' | grep -v __pycache__
```

### 2. Get Current Production Database Status
```bash
# Connect to production and check current migration version
# Option A: If you have direct database access
psql $PRODUCTION_DATABASE_URL -c "SELECT version_num FROM alembic_version;"

# Option B: Using Railway CLI
railway run alembic current

# Option C: Create a temporary script to check
railway run python -c "
from sqlalchemy import create_engine, text
import os
engine = create_engine(os.environ['DATABASE_URL'])
with engine.connect() as conn:
    result = conn.execute(text('SELECT version_num FROM alembic_version'))
    print('Current version:', result.fetchone()[0])
"
```

### 3. Compare Migration History
```bash
# Show migration history and pending migrations
railway run alembic history --verbose

# Check what migrations would be applied
railway run alembic upgrade --sql head
```

### 4. Verify Schema Consistency
```bash
# Generate a migration to check if schema matches expectations
railway run alembic revision --autogenerate -m "check_schema_drift"

# Review the generated migration file
# If it's empty or only contains minor changes, schema is in sync
```

### 5. Check for Missing Tables/Columns
```bash
# List all tables in production
railway run python -c "
from sqlalchemy import create_engine, inspect
import os
engine = create_engine(os.environ['DATABASE_URL'])
inspector = inspect(engine)
tables = inspector.get_table_names()
print('Tables:', sorted(tables))
"

# Compare with expected tables from models
railway run python -c "
from local_newsifier.models import *
from sqlmodel import SQLModel
tables = [table.__tablename__ for table in SQLModel.__subclasses__() if hasattr(table, '__tablename__')]
print('Expected tables:', sorted(tables))
"
```

### 6. Safe Migration Strategy

If migrations are needed:

1. **Backup First**
   ```bash
   # Create a database backup
   railway run pg_dump $DATABASE_URL > production_backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Test Migration Path**
   ```bash
   # Clone production data to staging
   # Test migration on staging first
   ```

3. **Apply Migrations**
   ```bash
   # Show pending migrations
   railway run alembic upgrade --sql head

   # Apply migrations one by one
   railway run alembic upgrade +1  # Apply next migration

   # Or apply all at once (after testing)
   railway run alembic upgrade head
   ```

## Quick Check Commands

For a quick status check, run these in order:

```bash
# 1. Show current version
railway run alembic current

# 2. Show migration history
railway run alembic history

# 3. Check for schema drift
railway run alembic check
```

## Red Flags to Watch For

- [ ] Multiple heads in migration history
- [ ] Missing alembic_version table
- [ ] Schema differences between models and database
- [ ] Migrations that would drop data
- [ ] Foreign key constraint violations

## Recovery Options

If issues are found:

1. **Missing alembic_version table**:
   ```bash
   railway run alembic stamp head  # Mark as current version
   ```

2. **Multiple heads**:
   ```bash
   railway run alembic merge -m "merge heads"
   ```

3. **Schema drift**:
   - Generate migration to sync
   - Or manually adjust and stamp

## Notes

- Always backup before any migration operations
- Test migration path on a copy of production data first
- Consider maintenance window for significant migrations
- Document any manual interventions
