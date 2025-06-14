web: bash scripts/init_spacy_models.sh && bash scripts/run_migrations_safe.sh && python -m uvicorn local_newsifier.api.main:app --host 0.0.0.0 --port $PORT
worker: bash scripts/init_spacy_models.sh && bash scripts/init_celery_worker.sh --concurrency=2
beat: bash scripts/init_spacy_models.sh && bash scripts/init_celery_beat.sh
