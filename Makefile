# Makefile for Local Newsifier project

.PHONY: help install setup-pyenv setup-poetry setup-dev setup-spacy test lint format clean run-api run-worker run-beat run-all-celery docker-build docker-up docker-down docker-test docker-restart

help:
	@echo "Available commands:"
	@echo " Environment Setup:"
	@echo "  make setup-dev         - Setup complete development environment"
	@echo "  make setup-pyenv       - Setup Python version with pyenv"
	@echo "  make setup-poetry      - Setup Poetry and install dependencies"
	@echo "  make setup-spacy       - Install spaCy models"
	@echo " Docker Commands:"
	@echo "  make docker-build      - Build development Docker containers"
	@echo "  make docker-up         - Start development environment with Docker"
	@echo "  make docker-down       - Stop development Docker environment"
	@echo "  make docker-test       - Run tests in Docker environment"
	@echo "  make docker-restart    - Restart Docker containers"
	@echo " Local Development:"
	@echo "  make install           - Install dependencies (legacy, use setup-poetry instead)"
	@echo "  make test              - Run tests"
	@echo "  make lint              - Run linting"
	@echo "  make format            - Format code"
	@echo "  make clean             - Clean build artifacts"
	@echo "  make run-api           - Run FastAPI application"
	@echo "  make run-worker        - Run Celery worker"
	@echo "  make run-beat          - Run Celery beat scheduler"
	@echo "  make run-all-celery    - Run Celery worker and beat in separate processes"

# Complete development setup
setup-dev: setup-pyenv setup-poetry setup-spacy

# Setup pyenv with correct Python version
setup-pyenv:
	@echo "Setting up Python environment with pyenv..."
	@if command -v pyenv 1>/dev/null 2>&1; then \
		echo "Installing Python 3.12.3 with pyenv..."; \
		pyenv install -s 3.12.3; \
		pyenv local 3.12.3; \
		echo "Python 3.12.3 installed and set as local version"; \
	else \
		echo "pyenv not found. Please install pyenv first:"; \
		echo "  On macOS: brew install pyenv"; \
		echo "  On Linux: curl https://pyenv.run | bash"; \
		exit 1; \
	fi

# Setup Poetry and install dependencies
setup-poetry:
	@echo "Setting up Poetry and installing dependencies..."
	@if ! command -v poetry 1>/dev/null 2>&1; then \
		echo "Installing Poetry..."; \
		curl -sSL https://install.python-poetry.org | python3 -; \
	fi
	poetry env use python
	poetry install --no-interaction
	@echo "Poetry setup complete. Use 'poetry shell' to activate environment."

# Legacy installation
install:
	pip install -e .

# Setup spaCy models
setup-spacy:
	@echo "Installing spaCy models..."
	poetry run python -m spacy download en_core_web_sm
	poetry run python -m spacy download en_core_web_lg
	@echo "spaCy models installed successfully"

# Docker commands
docker-build:
	docker-compose -f docker-compose.dev.yml build

docker-up:
	docker-compose -f docker-compose.dev.yml up -d

docker-down:
	docker-compose -f docker-compose.dev.yml down

docker-test:
	docker-compose -f docker-compose.dev.yml run --rm app pytest

docker-restart:
	docker-compose -f docker-compose.dev.yml restart

# Testing
test:
	poetry run pytest

# Linting
lint:
	poetry run flake8 src tests

# Formatting
format:
	poetry run black src tests

# Cleaning
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +

# Run FastAPI application
run-api: setup-spacy
	poetry run uvicorn local_newsifier.api.main:app --reload --host 0.0.0.0 --port 8000

# Run Celery worker
run-worker: setup-spacy
	poetry run celery -A local_newsifier.celery_app worker --loglevel=info

# Run Celery beat scheduler
run-beat: setup-spacy
	poetry run celery -A local_newsifier.celery_app beat --loglevel=info

# Run Celery worker and beat (for development)
run-all-celery: setup-spacy
	@echo "Starting Celery worker and beat..."
	@echo "Worker output: celery-worker.log"
	@echo "Beat output: celery-beat.log"
	@trap 'kill %1 %2; echo "Celery processes stopped"; exit 0' SIGINT;
	poetry run celery -A local_newsifier.celery_app worker --loglevel=info > celery-worker.log 2>&1 & \
	poetry run celery -A local_newsifier.celery_app beat --loglevel=info > celery-beat.log 2>&1 & \
	echo "Celery worker and beat running. Press Ctrl+C to stop."; \
	wait
