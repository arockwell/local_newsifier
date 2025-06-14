#!/bin/bash
# Diagnostic script for Alembic deployment issues
set -e

echo "=== Alembic Deployment Diagnostics ==="
echo "Time: $(date)"
echo "Environment: ${RAILWAY_ENVIRONMENT:-local}"
echo ""

# Function to safely run Python code
run_python() {
    python -c "$1" 2>&1 || echo "Python execution failed"
}

# 1. Check environment variables
echo "1. Environment Variables:"
echo "   DATABASE_URL: ${DATABASE_URL:+[SET]}"
echo "   POSTGRES_HOST: ${POSTGRES_HOST:-[NOT SET]}"
echo "   POSTGRES_PORT: ${POSTGRES_PORT:-[NOT SET]}"
echo "   POSTGRES_DB: ${POSTGRES_DB:-[NOT SET]}"
echo "   POSTGRES_USER: ${POSTGRES_USER:-[NOT SET]}"
echo "   POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:+[SET]}"
echo ""

# 2. Test database connection
echo "2. Database Connection Test:"
DB_TEST=$(run_python "
import sys
from sqlalchemy import create_engine, text
try:
    from local_newsifier.config.settings import get_settings
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text('SELECT version()'))
        version = result.scalar()
        print(f'Connected to: {version}')
except Exception as e:
    print(f'Connection failed: {type(e).__name__}: {str(e)}')
    sys.exit(1)
")
echo "   $DB_TEST"
echo ""

# 3. Check Alembic configuration
echo "3. Alembic Configuration:"
if [ -f "alembic.ini" ]; then
    echo "   alembic.ini: Found"
    SCRIPT_LOCATION=$(grep "script_location" alembic.ini | cut -d'=' -f2 | xargs)
    echo "   Script location: $SCRIPT_LOCATION"
else
    echo "   alembic.ini: NOT FOUND"
fi
echo ""

# 4. Check migration files
echo "4. Migration Files:"
if [ -d "alembic/versions" ]; then
    MIGRATION_COUNT=$(ls -1 alembic/versions/*.py 2>/dev/null | wc -l)
    echo "   Migration files found: $MIGRATION_COUNT"
    echo "   Latest migrations:"
    ls -1t alembic/versions/*.py 2>/dev/null | head -3 | while read file; do
        basename "$file"
    done
else
    echo "   Migration directory NOT FOUND"
fi
echo ""

# 5. Current Alembic state
echo "5. Current Migration State:"
ALEMBIC_CURRENT=$(alembic current 2>&1 || echo "Command failed")
echo "   $ALEMBIC_CURRENT"
echo ""

# 6. Database tables
echo "6. Database Tables:"
TABLES=$(run_python "
from sqlalchemy import inspect, create_engine
try:
    from local_newsifier.config.settings import get_settings
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)
    tables = sorted(inspector.get_table_names())
    if tables:
        for table in tables:
            print(f'   - {table}')
    else:
        print('   No tables found')
except Exception as e:
    print(f'   Error listing tables: {str(e)}')
")
echo "$TABLES"
echo ""

# 7. Alembic version table check
echo "7. Alembic Version Table:"
VERSION_CHECK=$(run_python "
from sqlalchemy import create_engine, text
try:
    from local_newsifier.config.settings import get_settings
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        # Check if table exists
        result = conn.execute(text(\"\"\"
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'alembic_version'
            );
        \"\"\"))
        exists = result.scalar()

        if exists:
            # Get current version
            result = conn.execute(text('SELECT version_num FROM alembic_version'))
            versions = [row[0] for row in result]
            if versions:
                print(f'   Table exists with version(s): {versions}')
            else:
                print('   Table exists but is empty')
        else:
            print('   Table does not exist')
except Exception as e:
    print(f'   Error checking version: {str(e)}')
")
echo "$VERSION_CHECK"
echo ""

# 8. Schema validation
echo "8. Schema Validation:"
SCHEMA_CHECK=$(run_python "
from sqlalchemy import inspect, create_engine
try:
    from local_newsifier.config.settings import get_settings
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)

    # Check for expected tables
    expected_tables = ['articles', 'entities', 'analysis_results', 'rss_feeds', 'apify_source_configs']
    existing = set(inspector.get_table_names())

    missing = set(expected_tables) - existing
    if missing:
        print(f'   Missing tables: {missing}')
    else:
        print('   All expected tables exist')

    # Check for critical columns
    if 'articles' in existing:
        columns = [col['name'] for col in inspector.get_columns('articles')]
        if 'title' in columns:
            # Check if title is nullable (latest migration)
            for col in inspector.get_columns('articles'):
                if col['name'] == 'title':
                    print(f'   articles.title nullable: {col[\"nullable\"]}')
                    break
except Exception as e:
    print(f'   Error validating schema: {str(e)}')
")
echo "$SCHEMA_CHECK"
echo ""

# 9. Recent deployment logs hint
echo "9. Debugging Tips:"
echo "   - Check Railway deployment logs for specific errors"
echo "   - Look for 'sqlalchemy.exc' exceptions"
echo "   - Verify DATABASE_URL format is correct"
echo "   - Ensure network connectivity to database"
echo "   - Check for concurrent migration attempts"
echo ""

# 10. Recommended actions
echo "10. Recommended Actions:"
if [[ $ALEMBIC_CURRENT == *"No such file or directory"* ]]; then
    echo "   ⚠️  Alembic not installed or not in PATH"
elif [[ $ALEMBIC_CURRENT == *"head"* ]]; then
    echo "   ✅ Migrations are up to date"
elif [[ $VERSION_CHECK == *"does not exist"* ]]; then
    echo "   ⚠️  Run: bash scripts/init_alembic.sh"
else
    echo "   ⚠️  Run: bash scripts/run_migrations_safe.sh"
fi
