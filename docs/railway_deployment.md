# Railway Deployment Guide

## Python Version Configuration

This project requires Python 3.12.10 for all environments. Railway deployments must set the following environment variable to ensure the correct Python version:

```
NIXPACKS_PYTHON_VERSION=3.12.10
```

## Environment Variables

The following environment variables must be configured in Railway:

### Database Configuration
- `POSTGRES_USER`: PostgreSQL username
- `POSTGRES_PASSWORD`: PostgreSQL password
- `POSTGRES_HOST`: PostgreSQL host
- `POSTGRES_PORT`: PostgreSQL port (usually 5432)
- `POSTGRES_DB`: PostgreSQL database name

### Celery Configuration
- `CELERY_BROKER_URL`: Redis URL for Celery broker
- `CELERY_RESULT_BACKEND`: Redis URL for Celery results

### Apify Integration
- `APIFY_TOKEN`: Your Apify API token (required for web scraping)

### Python Version
- `NIXPACKS_PYTHON_VERSION`: Must be set to `3.12.10`

## Deployment Process

1. Set all required environment variables in Railway dashboard
2. Deploy from GitHub repository
3. Railway will use Nixpacks to build and deploy the application
4. The `.python-version` file and `NIXPACKS_PYTHON_VERSION` ensure Python 3.12.10 is used

## Processes

The `railway.json` file configures three processes:
- **web**: FastAPI web interface
- **worker**: Celery worker for background tasks
- **beat**: Celery beat for scheduled tasks

Each process runs the necessary initialization scripts before starting.
