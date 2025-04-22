#!/bin/bash
# Initialize Alembic for an existing database
# This script "stamps" the database with the current migration
# without trying to recreate tables that already exist

# Check if the initial migration has already been applied
CURRENT=$(alembic current)

if [[ $CURRENT == *"head"* ]]; then
    echo "Migrations already initialized. Current version: $CURRENT"
else
    echo "Initializing Alembic on existing database..."
    # This marks the current database state as being at the latest migration
    # without trying to run any migrations (which would fail because tables already exist)
    alembic stamp head
    echo "Database stamped with current migration version"
fi

echo "Ready for future migrations!"
