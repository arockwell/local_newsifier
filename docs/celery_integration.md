# Celery Integration Guide

Celery was previously used for background task processing in Local Newsifier. The project has since removed Celery, and tasks now run synchronously. The information below is retained for historical reference.

## Legacy Information

The following sections describe the old Celery setup. They are no longer required but are kept here for reference.

### Required Environment Variables

- `CELERY_BROKER_URL` – Redis connection string (e.g. `redis://localhost:6379/0`)
- `CELERY_RESULT_BACKEND` – Redis connection string for results
- `APIFY_TOKEN` – Token used for Apify scraping

### Troubleshooting

- **Connection errors** – confirm Redis is running and the URLs are correct
- **No tasks processed** – ensure the worker is connected to the broker
- **Need more logs** – run with `--loglevel=debug` for verbose output

