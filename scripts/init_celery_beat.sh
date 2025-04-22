#!/bin/bash
# Initialize Celery beat scheduler for Local Newsifier
# This script ensures the database is properly set up before starting the Celery beat scheduler

set -e

# First ensure alembic migrations are up to date
echo "Applying database migrations..."
alembic upgrade head

# Start Celery beat with proper configuration
echo "Starting Celery beat scheduler..."
celery -A local_newsifier.celery_app beat --loglevel=info "$@"
