web: bash scripts/init_alembic.sh && alembic upgrade head && python -m uvicorn local_newsifier.api.main:app --host 0.0.0.0 --port $PORT
worker: bash scripts/init_celery_worker.sh --concurrency=2
beat: bash scripts/init_celery_beat.sh
