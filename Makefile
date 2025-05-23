# Makefile for Local Newsifier project
# Redesigned for clarity and simplicity

.PHONY: help install install-offline install-dev clean test lint format \
        run-api run-worker run-beat run-all \
        build-wheels build-wheels-linux \
        db-init db-reset db-stats \
        check-deps

# Default target shows help
.DEFAULT_GOAL := help

# Configuration
PYTHON ?= python3
POETRY ?= poetry
PIP ?= pip
PLATFORM := $(shell uname -s | tr '[:upper:]' '[:lower:]')
ARCH := $(shell uname -m)

# Color codes for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help:
	@echo "$(GREEN)Local Newsifier - Development Makefile$(NC)"
	@echo ""
	@echo "$(YELLOW)Quick Start:$(NC)"
	@echo "  make install       - Complete setup (Poetry, dependencies, spaCy, database)"
	@echo "  make run-all       - Run API, worker, and beat scheduler"
	@echo ""
	@echo "$(YELLOW)Installation:$(NC)"
	@echo "  make install       - Complete online installation"
	@echo "  make install-offline - Install from pre-built wheels (no internet)"
	@echo "  make install-dev   - Install with development dependencies"
	@echo ""
	@echo "$(YELLOW)Development:$(NC)"
	@echo "  make test          - Run tests in parallel"
	@echo "  make test-serial   - Run tests serially (for debugging)"
	@echo "  make test-coverage - Run tests with coverage report"
	@echo "  make lint          - Run code linting"
	@echo "  make format        - Auto-format code"
	@echo "  make clean         - Remove build artifacts"
	@echo ""
	@echo "$(YELLOW)Running Services:$(NC)"
	@echo "  make run-api       - Run FastAPI server"
	@echo "  make run-worker    - Run Celery worker"
	@echo "  make run-beat      - Run Celery beat scheduler"
	@echo "  make run-all       - Run all services (API, worker, beat)"
	@echo ""
	@echo "$(YELLOW)Database:$(NC)"
	@echo "  make db-init       - Initialize cursor-specific database"
	@echo "  make db-reset      - Reset database (WARNING: deletes data)"
	@echo "  make db-stats      - Show database statistics"
	@echo ""
	@echo "$(YELLOW)Offline Support:$(NC)"
	@echo "  make build-wheels  - Build wheels for current platform"
	@echo "  make build-wheels-linux - Build Linux wheels using Docker"

# ===== INSTALLATION TARGETS =====

# Complete installation - this is what the user wants!
install: check-deps
	@echo "$(GREEN)Starting complete Local Newsifier installation...$(NC)"
	@echo "Step 1/4: Setting up Poetry environment..."
	@$(POETRY) install --no-interaction || (echo "$(RED)Poetry installation failed$(NC)" && exit 1)
	@echo "$(GREEN)✓ Poetry environment created$(NC)"

	@echo "Step 2/4: Installing spaCy language models..."
	@if $(POETRY) run python -c "import spacy" 2>/dev/null; then \
		if $(POETRY) run python -c "import spacy; spacy.load('en_core_web_sm')" 2>/dev/null; then \
			echo "$(GREEN)✓ en_core_web_sm already installed$(NC)"; \
		else \
			echo "Downloading en_core_web_sm..."; \
			$(POETRY) run python -m spacy download en_core_web_sm || echo "$(YELLOW)Warning: Failed to install en_core_web_sm$(NC)"; \
		fi; \
		if $(POETRY) run python -c "import spacy; spacy.load('en_core_web_lg')" 2>/dev/null; then \
			echo "$(GREEN)✓ en_core_web_lg already installed$(NC)"; \
		else \
			echo "Downloading en_core_web_lg..."; \
			$(POETRY) run python -m spacy download en_core_web_lg || echo "$(YELLOW)Warning: Failed to install en_core_web_lg$(NC)"; \
		fi; \
	else \
		echo "$(YELLOW)Warning: spaCy not installed yet, skipping model downloads$(NC)"; \
		echo "$(YELLOW)Run 'make setup-spacy' after installation completes$(NC)"; \
	fi
	@echo "$(GREEN)✓ spaCy setup complete$(NC)"

	@echo "Step 3/4: Initializing database..."
	@$(POETRY) run python scripts/init_cursor_db.py || (echo "$(RED)Database initialization failed$(NC)" && exit 1)
	@echo "$(GREEN)✓ Database initialized$(NC)"

	@echo "Step 4/4: Running database migrations..."
	@if [ -f .env.cursor ]; then \
		export $$(cat .env.cursor | xargs) && $(POETRY) run alembic upgrade head || echo "$(YELLOW)Warning: Migration failed$(NC)"; \
	else \
		$(POETRY) run alembic upgrade head || echo "$(YELLOW)Warning: Migration failed$(NC)"; \
	fi
	@echo "$(GREEN)✓ Installation complete!$(NC)"
	@echo ""
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  1. Activate the environment: poetry shell"
	@echo "  2. Run the application: make run-all"
	@echo "  3. Visit http://localhost:8000"

# Offline installation from pre-built wheels
# This target automatically detects your platform and uses the appropriate wheels directory
# Platform detection: py<version>-<os>-<arch> (e.g., py312-macos-arm64)
# Falls back to version-only directory if platform-specific not found
install-offline: check-deps
	@echo "$(GREEN)Starting offline installation...$(NC)"
	@if [ ! -d "wheels" ]; then \
		echo "$(RED)Error: wheels directory not found$(NC)"; \
		echo "Run 'make build-wheels' first to download dependencies"; \
		exit 1; \
	fi

	@echo "Detecting platform..."
	$(eval PY_VERSION := $(shell $(PYTHON) -c "import sys; print(f'py{sys.version_info.major}{sys.version_info.minor}')"))
	$(eval OS_TYPE := $(shell uname | tr '[:upper:]' '[:lower:]' | sed 's/darwin/macos/'))
	$(eval ARCH := $(shell uname -m | sed 's/x86_64/x64/' | sed 's/aarch64/arm64/'))
	$(eval WHEELS_PATH := wheels/$(PY_VERSION)-$(OS_TYPE)-$(ARCH))
	$(eval FALLBACK_PATH := wheels/$(PY_VERSION))

	@echo "Platform: $(PY_VERSION)-$(OS_TYPE)-$(ARCH)"
	@if [ -d "$(WHEELS_PATH)" ]; then \
		echo "Using platform-specific wheels: $(WHEELS_PATH)"; \
		WHEELS_DIR="$(WHEELS_PATH)"; \
	elif [ -d "$(FALLBACK_PATH)" ]; then \
		echo "Using version-specific wheels: $(FALLBACK_PATH)"; \
		WHEELS_DIR="$(FALLBACK_PATH)"; \
	else \
		echo "$(RED)Error: No wheels found for $(PY_VERSION) on $(OS_TYPE)-$(ARCH)$(NC)"; \
		echo "Available wheel directories:"; \
		ls -la wheels/; \
		exit 1; \
	fi; \
	\
	echo "Step 1/4: Creating Poetry environment..."; \
	$(POETRY) env use $(PYTHON); \
	\
	echo "Step 2/4: Installing dependencies from wheels..."; \
	$(POETRY) run pip install --no-index --find-links="$$WHEELS_DIR" -r requirements.txt || exit 1; \
	$(POETRY) run pip install --no-index --find-links="$$WHEELS_DIR" -r requirements-dev.txt || exit 1; \
	\
	echo "Step 3/4: Installing local package..."; \
	$(POETRY) run pip install -e . || exit 1; \
	\
	echo "Step 4/4: Setting up database..."; \
	$(MAKE) db-init

	@echo "$(YELLOW)Note: spaCy models must be manually provided for offline installation$(NC)"
	@echo "$(GREEN)✓ Offline installation complete!$(NC)"

# Development installation with extra dependencies
install-dev: install
	@echo "$(GREEN)Installing development dependencies...$(NC)"
	@$(POETRY) install --with dev --no-interaction
	@echo "$(GREEN)✓ Development setup complete$(NC)"

# ===== DEPENDENCY CHECKING =====

check-deps:
	@echo "Checking dependencies..."
	@which $(POETRY) > /dev/null || (echo "$(RED)Error: Poetry not found. Install from https://python-poetry.org$(NC)" && exit 1)
	@which $(PYTHON) > /dev/null || (echo "$(RED)Error: Python not found$(NC)" && exit 1)
	@$(PYTHON) -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" || \
		(echo "$(RED)Error: Python 3.10+ required$(NC)" && exit 1)
	@echo "$(GREEN)✓ All dependencies satisfied$(NC)"

# ===== DATABASE MANAGEMENT =====

db-init:
	@echo "$(GREEN)Checking database initialization...$(NC)"
	@$(POETRY) run python scripts/init_cursor_db.py
	@if [ -f .env.cursor ]; then \
		echo "$(GREEN)✓ Database ready. Environment saved to .env.cursor$(NC)"; \
	else \
		echo "$(YELLOW)Warning: Database initialized but .env.cursor not created$(NC)"; \
	fi

db-reset:
	@echo "$(RED)WARNING: This will delete all data!$(NC)"
	@echo "Press Ctrl+C to cancel, or wait 5 seconds to continue..."
	@sleep 5
	@$(POETRY) run python scripts/reset_db.py
	@echo "$(GREEN)✓ Database reset complete$(NC)"

db-stats:
	@echo "$(GREEN)Database Statistics:$(NC)"
	@$(POETRY) run nf db stats

# ===== TESTING =====

test:
	@echo "$(GREEN)Running tests in parallel...$(NC)"
	@$(POETRY) run pytest -n auto

test-serial:
	@echo "$(GREEN)Running tests serially...$(NC)"
	@$(POETRY) run pytest -n 0

test-coverage:
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	@$(POETRY) run pytest --cov=src/local_newsifier --cov-report=term-missing --cov-report=html
	@echo "$(GREEN)✓ Coverage report generated in htmlcov/$(NC)"

# ===== CODE QUALITY =====

lint:
	@echo "$(GREEN)Running linters...$(NC)"
	@$(POETRY) run flake8 src tests || echo "$(YELLOW)Linting issues found$(NC)"
	@$(POETRY) run mypy src || echo "$(YELLOW)Type checking issues found$(NC)"

format:
	@echo "$(GREEN)Formatting code...$(NC)"
	@$(POETRY) run isort src tests
	@$(POETRY) run black src tests
	@echo "$(GREEN)✓ Code formatted$(NC)"

# ===== RUNNING SERVICES =====

run-api:
	@echo "$(GREEN)Starting FastAPI server...$(NC)"
	@if [ -f .env.cursor ]; then \
		export $$(cat .env.cursor | xargs); \
	fi; \
	$(POETRY) run uvicorn local_newsifier.api.main:app --reload --host 0.0.0.0 --port 8000

run-worker:
	@echo "$(GREEN)Starting Celery worker...$(NC)"
	@if [ -f .env.cursor ]; then \
		export $$(cat .env.cursor | xargs); \
	fi; \
	$(POETRY) run celery -A local_newsifier.celery_app worker --loglevel=info

run-beat:
	@echo "$(GREEN)Starting Celery beat scheduler...$(NC)"
	@if [ -f .env.cursor ]; then \
		export $$(cat .env.cursor | xargs); \
	fi; \
	$(POETRY) run celery -A local_newsifier.celery_app beat --loglevel=info

run-all:
	@echo "$(GREEN)Starting all services...$(NC)"
	@echo "API: http://localhost:8000"
	@echo "Worker logs: celery-worker.log"
	@echo "Beat logs: celery-beat.log"
	@echo "Press Ctrl+C to stop all services"
	@echo ""
	@if [ -f .env.cursor ]; then \
		export $$(cat .env.cursor | xargs); \
	fi; \
	trap 'kill %1 %2 %3 2>/dev/null; echo "\n$(GREEN)All services stopped$(NC)"; exit 0' SIGINT; \
	$(POETRY) run uvicorn local_newsifier.api.main:app --reload --host 0.0.0.0 --port 8000 & \
	$(POETRY) run celery -A local_newsifier.celery_app worker --loglevel=info > celery-worker.log 2>&1 & \
	$(POETRY) run celery -A local_newsifier.celery_app beat --loglevel=info > celery-beat.log 2>&1 & \
	tail -f celery-worker.log celery-beat.log

# ===== WHEEL BUILDING =====

build-wheels:
	@echo "$(GREEN)Building wheels for $(PLATFORM)-$(ARCH)...$(NC)"
	@./scripts/build_wheels.sh
	@echo "$(GREEN)✓ Wheels built successfully$(NC)"

build-wheels-linux:
	@echo "$(GREEN)Building Linux wheels using Docker...$(NC)"
	@./scripts/build_linux_wheels.sh 3.12
	@echo "$(GREEN)✓ Linux wheels built successfully$(NC)"

# ===== CLEANUP =====

clean:
	@echo "$(GREEN)Cleaning build artifacts...$(NC)"
	@rm -rf build/ dist/ *.egg-info
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name ".coverage" -delete
	@rm -rf htmlcov/
	@rm -f celery-worker.log celery-beat.log
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

# ===== ADVANCED TARGETS =====

# These targets are preserved for backward compatibility but not shown in main help
setup-poetry: install
setup-poetry-offline: install-offline
setup-spacy:
	@echo "$(GREEN)Checking spaCy models...$(NC)"
	@if $(POETRY) run python -c "import spacy; spacy.load('en_core_web_sm')" 2>/dev/null; then \
		echo "$(GREEN)✓ en_core_web_sm already installed$(NC)"; \
	else \
		echo "Installing en_core_web_sm..."; \
		$(POETRY) run python -m spacy download en_core_web_sm; \
	fi
	@if $(POETRY) run python -c "import spacy; spacy.load('en_core_web_lg')" 2>/dev/null; then \
		echo "$(GREEN)✓ en_core_web_lg already installed$(NC)"; \
	else \
		echo "Installing en_core_web_lg..."; \
		$(POETRY) run python -m spacy download en_core_web_lg; \
	fi
setup-db: db-init
organize-wheels:
	@./scripts/organize_wheels.sh
test-wheels:
	@echo "$(GREEN)Testing offline installation...$(NC)"
	@./scripts/test_offline_install.sh $(PYTHON)
build-wheels-all:
	@for py in python3.10 python3.11 python3.12 python3.13; do \
		if command -v $$py >/dev/null 2>&1; then \
			echo "Building wheels for $$py..."; \
			./scripts/build_wheels.sh $$py; \
		fi; \
	done
