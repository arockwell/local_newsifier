# Makefile for Local Newsifier project

.PHONY: help install setup-spacy test lint format clean run-api run-worker run-beat run-all-celery

help:
	@echo "Available commands:"
	@echo "  make install           - Install dependencies"
	@echo "  make setup-spacy       - Install spaCy model (en_core_web_lg)"
	@echo "  make test              - Run tests"
	@echo "  make lint              - Run linting"
	@echo "  make format            - Format code"
	@echo "  make clean             - Clean build artifacts"
	@echo "  make run-api           - Run FastAPI application"
	@echo "  make run-worker        - Run Celery worker"
	@echo "  make run-beat          - Run Celery beat scheduler"
	@echo "  make run-all-celery    - Run Celery worker and beat in separate processes"

# Installation
install:
	pip install -e .

# Setup spaCy models
setup-spacy:
	bash scripts/init_spacy_models.sh

# Testing
test:
	pytest

# Linting
lint:
	flake8 src tests

# Formatting
format:
	black src tests

# Cleaning
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +

# Run FastAPI application
run-api: setup-spacy
	uvicorn local_newsifier.api.main:app --reload --host 0.0.0.0 --port 8000

# Run Celery worker
run-worker: setup-spacy
	celery -A local_newsifier.celery_app worker --loglevel=info

# Run Celery beat scheduler
run-beat: setup-spacy
	celery -A local_newsifier.celery_app beat --loglevel=info

# Run Celery worker and beat (for development)
run-all-celery: setup-spacy
	@echo "Starting Celery worker and beat..."
	@echo "Worker output: celery-worker.log"
	@echo "Beat output: celery-beat.log"
	@trap 'kill %1 %2; echo "Celery processes stopped"; exit 0' SIGINT;
	celery -A local_newsifier.celery_app worker --loglevel=info > celery-worker.log 2>&1 & \
	celery -A local_newsifier.celery_app beat --loglevel=info > celery-beat.log 2>&1 & \
	echo "Celery worker and beat running. Press Ctrl+C to stop."; \
	wait
