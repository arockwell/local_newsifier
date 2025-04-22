#!/bin/bash
# Initialize Celery worker for Local Newsifier
# This script ensures the database is properly set up before starting the Celery worker

set -e

# First ensure alembic migrations are up to date
echo "Applying database migrations..."
alembic upgrade head

# Start Celery worker with proper configuration
echo "Starting Celery worker..."
celery -A local_newsifier.celery_app worker --loglevel=info "$@"
