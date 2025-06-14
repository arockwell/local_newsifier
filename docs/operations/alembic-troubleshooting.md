# Alembic Troubleshooting Guide

## Overview

This guide helps diagnose and fix Alembic migration issues in production deployments.

## Quick Diagnosis

Run the diagnostic script to check your deployment state:

```bash
bash scripts/diagnose_alembic.sh
```

## Common Issues and Solutions

### 1. "No module named 'alembic'" Error

**Symptom**: Deployment fails with import error for Alembic.

**Solution**:
- Ensure `alembic` is in `requirements.txt`
- Check that dependencies are installed before running migrations

### 2. Database Connection Failures

**Symptom**: Migration scripts fail to connect to database.

**Common Causes**:
- Missing or incorrect `DATABASE_URL` environment variable
- Network connectivity issues
- PostgreSQL service not ready

**Solution**:
- Verify all database environment variables are set in Railway
- Use the diagnostic script to test connection
- Add retry logic to handle temporary connection issues

### 3. Migration State Mismatch

**Symptom**:
- Tables exist but Alembic doesn't recognize them
- `alembic current` shows no version but database has tables

**Solution**:
```bash
# If you're sure the database matches the latest schema:
alembic stamp head

# If unsure, use the safe migration script:
bash scripts/run_migrations_safe.sh
```

### 4. Concurrent Migration Attempts

**Symptom**:
- Lock timeout errors
- Partial migrations
- Duplicate key violations in alembic_version

**Solution**:
- The new `run_migrations_safe.sh` script includes lock management
- Ensure only one instance runs migrations (handled automatically)

### 5. Fresh Deployment Issues

**Symptom**: New Railway deployments fail to initialize database.

**Solution**:
1. Check that PostgreSQL service is provisioned and linked
2. Verify environment variables are set
3. Use the safe migration script which handles fresh databases

## Migration Scripts

### `scripts/init_alembic.sh` (Legacy)
The original initialization script. Has issues with:
- Poor error handling
- Can incorrectly stamp databases
- No lock management

### `scripts/run_migrations_safe.sh` (Recommended)
New robust migration runner with:
- Proper error handling
- Lock management to prevent concurrent runs
- Detailed logging
- State verification
- Automatic recovery for common issues

### `scripts/diagnose_alembic.sh`
Diagnostic tool that checks:
- Environment variables
- Database connectivity
- Migration files
- Current migration state
- Schema validation

## Best Practices

1. **Always backup before migrations**:
   ```bash
   pg_dump $DATABASE_URL > backup.sql
   ```

2. **Test migrations locally first**:
   ```bash
   alembic upgrade head
   alembic downgrade -1
   alembic upgrade head
   ```

3. **Monitor deployment logs**:
   - Watch for SQLAlchemy exceptions
   - Check for connection timeouts
   - Look for lock conflicts

4. **Use staging environment**:
   - Test deployment process in staging
   - Verify migration scripts work correctly

## Recovery Procedures

### Reset Migration State (Data Loss!)
```bash
# Only if you can afford to lose all data
alembic downgrade base
alembic upgrade head
```

### Manual State Correction
```bash
# Check current schema
psql $DATABASE_URL -c "\dt"

# If schema matches a known revision
alembic stamp <revision-id>

# Then run pending migrations
alembic upgrade head
```

### Emergency Rollback
```bash
# Rollback last migration
alembic downgrade -1

# Or rollback to specific revision
alembic downgrade <revision-id>
```

## Railway-Specific Tips

1. **Environment Variables**: Set in Railway dashboard, not in code
2. **Build Commands**: Update in `railway.json`
3. **Health Checks**: Don't include migration status in health endpoint
4. **Logs**: Use Railway CLI to tail logs during deployment

## Getting Help

If issues persist:
1. Run `scripts/diagnose_alembic.sh` and save output
2. Check Railway deployment logs
3. Look for specific SQLAlchemy error messages
4. Consider manual database inspection with psql
