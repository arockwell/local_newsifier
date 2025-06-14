#!/bin/bash
# Initialize Alembic and create tables if needed
set -e

echo "Starting database initialization..."

# Function to check if alembic_version table exists
check_alembic_table() {
    python -c "
import sys
from sqlalchemy import inspect, create_engine, text
from local_newsifier.config.settings import get_settings

try:
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        # Check for alembic_version table
        result = conn.execute(text(\"\"\"
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'alembic_version'
            );
        \"\"\"))
        exists = result.scalar()
        print('exists' if exists else 'not_exists')
except Exception as e:
    print(f'error: {str(e)}', file=sys.stderr)
    sys.exit(1)
" 2>&1
}

# Function to get current revision
get_current_revision() {
    alembic current 2>/dev/null | grep -oE '[a-f0-9]{12}' | head -1 || echo "none"
}

# Function to check if any tables exist
check_tables_exist() {
    python -c "
import sys
from sqlalchemy import inspect, create_engine
from local_newsifier.config.settings import get_settings

try:
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    # Check for any of our known tables
    our_tables = {'articles', 'entities', 'analysis_results', 'rss_feeds', 'apify_source_configs'}
    exists = bool(our_tables.intersection(tables))
    print('exists' if exists else 'not_exists')
except Exception as e:
    print(f'error: {str(e)}', file=sys.stderr)
    sys.exit(1)
" 2>&1
}

# Main logic
ALEMBIC_TABLE=$(check_alembic_table)
echo "Alembic table check: $ALEMBIC_TABLE"

if [[ $ALEMBIC_TABLE == "error"* ]]; then
    echo "ERROR: Failed to check alembic table: $ALEMBIC_TABLE"
    exit 1
fi

if [[ $ALEMBIC_TABLE == "not_exists" ]]; then
    echo "No alembic_version table found. Checking if other tables exist..."
    TABLES_EXIST=$(check_tables_exist)

    if [[ $TABLES_EXIST == "exists" ]]; then
        echo "WARNING: Tables exist but no alembic_version table!"
        echo "This indicates a database in an inconsistent state."
        echo "Creating alembic_version table and stamping with latest revision..."

        # Create the alembic_version table manually
        python -c "
from sqlalchemy import create_engine, text
from local_newsifier.config.settings import get_settings
settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
with engine.connect() as conn:
    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS alembic_version (
            version_num VARCHAR(32) NOT NULL,
            CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
        );
    '''))
    conn.commit()
"
        # Stamp with the latest revision
        alembic stamp head
        echo "Database stamped with latest revision"
    else
        echo "No tables exist. Running all migrations..."
        alembic upgrade head
        echo "All migrations completed successfully"
    fi
else
    CURRENT_REV=$(get_current_revision)
    echo "Current revision: $CURRENT_REV"

    if [[ $CURRENT_REV == "none" ]]; then
        echo "ERROR: Alembic table exists but no revision set!"
        echo "Attempting to determine correct revision..."

        # Check if we have the latest schema by looking for the schedule_id column
        SCHEMA_CHECK=$(python -c "
from sqlalchemy import inspect, create_engine
from local_newsifier.config.settings import get_settings
settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
inspector = inspect(engine)
if 'apify_source_configs' in inspector.get_table_names():
    columns = [col['name'] for col in inspector.get_columns('apify_source_configs')]
    if 'schedule_id' in columns:
        print('latest')
    else:
        print('outdated')
else:
    print('missing')
" 2>&1)

        if [[ $SCHEMA_CHECK == "latest" ]]; then
            echo "Schema appears to be up to date. Stamping with head..."
            alembic stamp head
        else
            echo "Schema appears outdated or missing. Please manually verify and fix."
            exit 1
        fi
    else
        echo "Running pending migrations from $CURRENT_REV..."
        alembic upgrade head
        echo "Migrations completed successfully"
    fi
fi

echo "Database initialization complete!"
