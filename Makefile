# Makefile for Local Newsifier project

.PHONY: help install setup-poetry setup-spacy build-wheels test lint format clean run-api

help:
	@echo "Available commands:"
	@echo "  make install           - Install dependencies (legacy, use setup-poetry instead)"
	@echo "  make setup-poetry      - Setup Poetry and install dependencies"
	@echo "  make setup-spacy       - Install spaCy models"
	@echo "  make build-wheels      - Download dependency wheels"
	@echo "  make test              - Run tests in parallel (using all available CPU cores)"
	@echo "  make test-serial       - Run tests serially (for debugging)"
	@echo "  make lint              - Run linting"
	@echo "  make format            - Format code"
	@echo "  make clean             - Clean build artifacts"
       @echo "  make run-api           - Run FastAPI application"

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
	@echo "Building wheels into ./wheels..."
	./scripts/build_wheels.sh

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

