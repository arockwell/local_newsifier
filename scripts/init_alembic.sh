#!/bin/bash
# Initialize Alembic and create tables if needed

echo "Starting database initialization..."

# Try to get current migration state
CURRENT=$(alembic current 2>/dev/null || echo "None")

if [[ $CURRENT == *"head"* ]]; then
    echo "Migrations already initialized. Current version: $CURRENT"
else
    echo "Checking if tables exist..."
    
    # Use Python to check if tables exist instead of psql
    # This is more portable across deployment environments
    TABLE_CHECK=$(python -c "
import sys
from sqlalchemy import inspect
from sqlalchemy import create_engine
from local_newsifier.config.settings import settings

try:
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if 'articles' in tables:
        print('exists')
    else:
        print('not_exists')
except Exception as e:
    print(f'error: {str(e)}')
    sys.exit(1)
" || echo "error")
    
    if [[ $TABLE_CHECK == *"exists"* ]]; then
        echo "Tables exist but not tracked by Alembic. Stamping current state..."
        alembic stamp head
    elif [[ $TABLE_CHECK == *"not_exists"* ]]; then
        echo "Tables don't exist. Running migrations to create schema..."
        alembic upgrade head
        echo "Database schema created successfully"
    else
        echo "Error checking tables: $TABLE_CHECK"
        echo "Attempting to run migrations anyway..."
        # Try to run migrations regardless
        alembic upgrade head || echo "WARNING: Migration failed, but continuing deployment"
    fi
fi

echo "Database initialization complete!"
