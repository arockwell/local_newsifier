# Testing Guide

This document explains how to effectively run and optimize tests in the Local Newsifier project.

## Running Tests

### Basic Test Run

Run the entire test suite:

```bash
poetry run pytest
```

### Parallel Test Execution

Tests run in parallel by default. You can control the number of parallel processes:

```bash
# Use 4 processes
poetry run pytest -n 4

# Auto-detect CPU count
poetry run pytest -n auto
```

### Running Test Categories

You can run specific categories of tests:

```bash
# Run only fast tests (exclude slow tests)
poetry run pytest -m "not slow"

# Run only tests that require database connections
poetry run pytest -m "db"
```

## Test Markers

We use the following markers to categorize tests:

- `@pytest.mark.slow` - Tests that take longer than 1 second to run
- `@pytest.mark.db` - Tests that require database connections
- `@pytest.mark.fast` - Tests that are guaranteed to run quickly

## Optimizing Test Performance

### Identifying Slow Tests

You can identify which tests are slow by running:

```bash
poetry run python scripts/identify_slow_tests.py
```

This will generate a report showing the slowest tests and recommendations for improvement.

### Adding Slow Markers

When you identify a slow test, mark it with the `@pytest.mark.slow` decorator:

```python
@pytest.mark.slow
def test_my_slow_function():
    # Test implementation
```

### Using Test Mode for Database Operations

For tests that interact with the database, use the `test_mode=True` parameter to optimize database connection handling:

```python
# In tests
from local_newsifier.database.engine import get_engine

engine = get_engine(test_mode=True)
```

## Test Organization

Tests are organized by component type:

- `tests/api/` - API endpoint tests
- `tests/cli/` - Command-line interface tests
- `tests/crud/` - Database CRUD operation tests
- `tests/database/` - Database connection and configuration tests
- `tests/flows/` - Workflow and process flow tests
- `tests/models/` - Data model tests
- `tests/services/` - Business logic service tests
- `tests/tools/` - Processing tool tests