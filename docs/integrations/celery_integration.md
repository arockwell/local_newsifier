# Celery Integration Guide

This guide explains how to run Celery with Redis for background task processing in Local Newsifier.

## Running Workers

Celery relies on two settings:

- `settings.CELERY_BROKER_URL` – Redis URL used as the message broker
- `settings.CELERY_RESULT_BACKEND` – Redis URL used for storing task results

Start a worker using the provided Make target:

```bash
make run-worker
```

## Running Beat

The beat scheduler runs periodic tasks. Start it with:

```bash
make run-beat
```

## Running Both

For development, run worker and beat together:

```bash
make run-all-celery
```

## Required Environment Variables

Set these variables before running Celery:

- `CELERY_BROKER_URL` – Redis connection string (e.g. `redis://localhost:6379/0`)
- `CELERY_RESULT_BACKEND` – Redis connection string for results
- `APIFY_TOKEN` – Token used for Apify scraping

## Troubleshooting

- **Connection errors** – confirm Redis is running and the URLs are correct
- **No tasks processed** – ensure the worker is connected to the broker
- **Need more logs** – run with `--loglevel=debug` for verbose output
