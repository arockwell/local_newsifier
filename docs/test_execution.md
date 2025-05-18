# Test Execution Guide

This document explains how to run tests for the Local Newsifier project. Pytest-xdist can be used for parallel execution, but tests run serially by default.

## Test Configuration

The Local Newsifier project uses pytest with the following components:

- **SQLite in-memory databases** for test isolation
- **pytest-xdist** for parallel test execution
- **pytest-cov** for test coverage reporting

## Running Tests

There are several ways to run tests in this project:

### Basic Test Execution

Run all tests serially using the default configuration:

```bash
make test  # Runs: poetry run pytest
```

Tests run without `pytest-xdist` by default because `pyproject.toml` sets `addopts = "-vs"`.
Parallel execution must be enabled manually.

### Serial Test Execution

The `make test` command already runs tests serially, but a dedicated target exists for clarity:

```bash
make test-serial  # Runs: poetry run pytest -n 0
```

Use this target when you want to be explicit about disabling parallel workers.

### Parallel Test Execution

To enable pytest-xdist and run tests across multiple workers, pass the `-n` option manually:

```bash
poetry run pytest -n auto  # Use all available CPU cores
```

You can also specify an explicit number of workers:

```bash
poetry run pytest -n 4  # Uses 4 worker processes
```

### Run Tests with Coverage Reporting

To see test coverage information:

```bash
make test-coverage  # Runs: poetry run pytest --cov=src/local_newsifier --cov-report=term-missing
```

### Run Tests for a Specific Module

To run tests for a specific part of the codebase:

```bash
poetry run pytest tests/api/  # Run all API tests
poetry run pytest tests/crud/test_article.py  # Run tests for a specific file
poetry run pytest tests/services/test_rss_feed_service.py::test_create_feed  # Run a specific test
```

## Test Isolation

Each test uses a clean, isolated in-memory SQLite database:

1. For serial test execution, a single in-memory database is used with transaction-level isolation.
2. For parallel test execution (with pytest-xdist), each worker gets its own dedicated database.

## Troubleshooting Test Failures

### Handling Database-Related Failures

If you encounter database-related test failures:

1. Try running the tests serially first to see if it's related to parallel execution.
2. Add debug logging to identify any transaction isolation issues:
   ```python
   import logging
   logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
   ```

### Common Issues

1. **SQLite in-memory databases** - These are isolated by process, so tests running in parallel with pytest-xdist shouldn't interfere with each other.

2. **Fixture dependencies** - Ensure fixtures don't have hidden cross-dependencies that would cause issues when run in parallel.

3. **Global state** - Avoid modifying global state in tests that could cause issues in parallel execution.

## Best Practices

1. **Keep tests isolated** - Each test should set up its own data and not rely on data created by other tests.

2. **Use fixtures appropriately** - Use function-scoped fixtures for most cases, and session-scoped only when necessary.

3. **Clean up after tests** - Use teardown to clean up resources, especially when using session-scoped fixtures.

4. **Avoid file I/O conflicts** - When tests write to files, use unique names or temporary directories to prevent conflicts.

5. **Be careful with class-scoped fixtures** - These are shared across all tests in a class, which might cause issues with parallel execution.
