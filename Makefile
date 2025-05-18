# Makefile for Local Newsifier project

.PHONY: help install setup-poetry setup-spacy build-wheels build-wheels-all build-linux-wheels organize-wheels test-wheels test lint format clean run-api run-worker run-beat run-all-celery

help:
	@echo "Available commands:"
	@echo "  make install           - Install dependencies (legacy, use setup-poetry instead)"
	@echo "  make setup-poetry      - Setup Poetry and install dependencies"
	@echo "  make setup-spacy       - Install spaCy models"
	@echo "  make build-wheels      - Build wheels for current Python version on current platform"
	@echo "  make build-wheels-all  - Build wheels for all supported Python versions on current platform"
	@echo "  make build-linux-wheels - Build wheels for Linux platforms using Docker"
	@echo "  make organize-wheels   - Organize existing wheels into version-specific and platform-specific directories" 
	@echo "  make test-wheels       - Test offline installation with current Python version on current platform"
	@echo "  make test              - Run tests in parallel (using all available CPU cores)"
	@echo "  make test-serial       - Run tests serially (for debugging)"
	@echo "  make lint              - Run linting"
	@echo "  make format            - Format code"
	@echo "  make clean             - Clean build artifacts"
	@echo "  make run-api           - Run FastAPI application"
	@echo "  make run-worker        - Run Celery worker"
	@echo "  make run-beat          - Run Celery beat scheduler"
	@echo "  make run-all-celery    - Run Celery worker and beat in separate processes"

# Legacy installation
install:
	pip install -e .

# Setup Poetry and install dependencies
setup-poetry:
	@echo "Installing dependencies with Poetry..."
	poetry install --no-interaction
	@echo "Poetry setup complete. Use 'poetry shell' to activate environment."

# Setup spaCy models
setup-spacy:
	@echo "Installing spaCy models..."
	poetry run python -m spacy download en_core_web_sm
	poetry run python -m spacy download en_core_web_lg
	@echo "spaCy models installed successfully"

# Build dependency wheels for offline installation
build-wheels:
	@echo "Building wheels for current Python version..."
	./scripts/build_wheels.sh

build-wheels-all:
	@echo "Building wheels for all supported Python versions..."
	@if command -v python3.10 >/dev/null 2>&1; then \
		echo "Building wheels for Python 3.10..."; \
		./scripts/build_wheels.sh python3.10; \
	else \
		echo "Python 3.10 not found, skipping"; \
	fi
	@if command -v python3.11 >/dev/null 2>&1; then \
		echo "Building wheels for Python 3.11..."; \
		./scripts/build_wheels.sh python3.11; \
	else \
		echo "Python 3.11 not found, skipping"; \
	fi
	@if command -v python3.12 >/dev/null 2>&1; then \
		echo "Building wheels for Python 3.12..."; \
		./scripts/build_wheels.sh python3.12; \
	else \
		echo "Python 3.12 not found, skipping"; \
	fi
	@if command -v python3.13 >/dev/null 2>&1; then \
		echo "Building wheels for Python 3.13..."; \
		./scripts/build_wheels.sh python3.13; \
	else \
		echo "Python 3.13 not found, skipping"; \
	fi
	@echo "Wheel building complete for all available Python versions"
	@echo "Don't forget to commit the wheels directory to the repository for offline installation."

build-linux-wheels:
	@echo "Building wheels for Linux platforms using Docker..."
	@echo "Building for Python 3.12..."
	./scripts/build_linux_wheels.sh 3.12
	@echo "Building for Python 3.13..."
	./scripts/build_linux_wheels.sh 3.13
	@echo "Linux wheel building complete"
	@echo "Don't forget to commit the wheels directory to the repository for offline installation."

organize-wheels:
	@echo "Organizing existing wheels into version-specific and platform-specific directories..."
	./scripts/organize_wheels.sh

test-wheels:
	@echo "Testing offline installation with current Python version..."
	./scripts/test_offline_install.sh

# Testing
test:
	poetry run pytest

# Run tests serially (non-parallel) if needed for debugging
test-serial:
	poetry run pytest -n 0

# Run tests with coverage report
test-coverage:
	poetry run pytest --cov=src/local_newsifier --cov-report=term-missing

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
