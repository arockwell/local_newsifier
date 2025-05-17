# Project Chronicle Persistence

[![Tests](https://github.com/alexrockwell/local_newsifier/actions/workflows/test.yml/badge.svg)](https://github.com/alexrockwell/local_newsifier/actions/workflows/test.yml)

A robust system for fetching, analyzing, and storing local news articles from Gainesville, FL using crew.ai Flows.

## Project Overview

This system automatically fetches local news articles, performs Named Entity Recognition (NER) analysis, and stores the results with a focus on reliability and observability.

## Features

- Automated news article fetching
- Named Entity Recognition (NER) analysis
- Headline trend analysis with NLP-powered keyword extraction
- Temporal tracking of trending terms in news coverage
- Web scraping via Apify integration for websites without RSS feeds
- Apify configuration management and scheduling via CLI ([README_CLI.md](README_CLI.md), [docs/apify_integration.md](docs/apify_integration.md))
- Robust error handling and retry mechanisms
- State persistence and workflow resumption
- Comprehensive logging and monitoring
- Dependency injection for modular and testable code

## Architecture

### Dependency Injection

Local Newsifier uses **fastapi-injectable** for all dependency injection. Provider
functions defined in `local_newsifier.di.providers` expose dependencies and are
injected with FastAPI's `Depends()` pattern.

For details on the architecture and testing strategies see:
- [DI Architecture Guide](docs/di_architecture.md)
- [Dependency Injection Guide](docs/dependency_injection.md)
- [fastapi-injectable Guide](docs/fastapi_injectable.md)

## Setup

1. Install Poetry (package manager):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Install dependencies:
```bash
poetry install
```

If your environment lacks internet access, generate the wheels directory on a
connected machine first:

```bash
make build-wheels
```

Copy the resulting `wheels/` directory and install from it locally:

```bash
pip install --no-index --find-links=wheels -r requirements.txt
```

3. Download spaCy model:
```bash
poetry run python -m spacy download en_core_web_lg
```

4. (Optional) Set up Apify Token:
```bash
# Create .env file with your Apify token
echo "APIFY_TOKEN=your_token_here" > .env
```

Note: While an Apify token is required for production use, the test suite can run without it. See [docs/testing_apify.md](docs/testing_apify.md) for more details.

## Usage

### Command Line Interface (CLI)

The system provides a command-line interface for managing RSS feeds and other operations:

```bash
# Activate Poetry shell
poetry shell

# Get help
nf --help

# Manage RSS feeds
nf feeds list              # List all feeds
nf feeds add <url>         # Add a new feed
nf feeds show <id>         # Show feed details
nf feeds process <id>      # Process a feed manually
```

For detailed CLI documentation, see [README_CLI.md](README_CLI.md).

### Apify Web Scraping

The system integrates with Apify for scraping content from websites without RSS feeds:

```bash
# Test Apify connection
nf apify test

# Scrape content from a website
nf apify scrape-content https://example.com

# Use web-scraper actor with custom selectors
nf apify web-scraper https://example.com --selector "article a"

# Get items from an Apify dataset
nf apify get-dataset <dataset_id>
```

For detailed Apify integration documentation, see [docs/apify_integration.md](docs/apify_integration.md).

### Scripts

Run the article processing pipeline:
```bash
poetry run python scripts/run_pipeline.py --url <URL>
```

Analyze headline trends:
```bash
# Analyze recent headlines
poetry run python scripts/demo_headline_trends.py --days 30 --interval day

# Generate a report in markdown format
poetry run python scripts/demo_headline_trends.py --format markdown --output trends.md

# Analyze a specific date range
poetry run python scripts/demo_headline_trends.py --start-date 2023-01-01 --end-date 2023-01-31 --interval week
```

## Testing Guide

### Continuous Integration

Tests are automatically run on:
- Every push to main branch
- Every pull request
- Python versions 3.10, 3.11, and 3.12

Test results and coverage reports are available in GitHub Actions:
- View test execution and logs
- Coverage reports are displayed in the test output
- XML coverage reports are generated for detailed analysis

### Running Tests

Basic test execution:
```bash
poetry run pytest
```

With coverage:
```bash
poetry run pytest --cov=src/local_newsifier
```

With detailed test output:
```bash
poetry run pytest -v --durations=0
```

### Test Structure

Tests are organized by component type:
```
tests/
├── flows/          # Flow-level tests
├── tools/          # Individual tool tests
└── models/         # Model/state tests
```

### Testing Best Practices

1. **Test Organization**
   - One test file per component
   - Test classes/functions mirror source structure
   - Clear, descriptive test names

2. **Fixture Usage**
   - Use session-scoped fixtures for expensive objects
   - Use function-scoped fixtures for test-specific data
   - Reset mutable fixture state between tests

3. **Mock Guidelines**
   - Mock external dependencies
   - Use side_effect for complex behaviors
   - Reset mocks between tests
   - Verify mock calls when behavior matters

4. **Performance**
   - Minimize wait times in retry tests
   - Use session-scoped fixtures for reusable objects
   - Mock time-consuming operations
   - Keep individual tests focused and fast

5. **Test Coverage**
   - Aim for high coverage (>90%)
   - Test happy paths and edge cases
   - Test error conditions
   - Test retry mechanisms

6. **Test Style**
   ```python
   def test_descriptive_name():
       """Test description in docstring."""
       # Setup
       initial_state = setup_test_state()

       # Execute
       result = component.do_something()

       # Verify
       assert result.status == expected_status
       assert component.mock.called_once()
   ```

### Recent Testing Architecture Changes

#### Environment Variable Handling
The testing framework now includes robust environment variable management:
- Tests that depend on default values now properly clear environment variables
- Environment variables are restored after tests, even if they fail
- Fixtures handle environment variable setup and teardown
- Example:
  ```python
  def test_with_clean_environment():
      # Store original environment
      original_env = {k: os.environ.get(k) for k in relevant_keys}

      try:
          # Clear environment for test
          for key in original_env:
              if key in os.environ:
                  del os.environ[key]

          # Run test with clean environment
          result = test_function()

      finally:
          # Restore original environment
          for key, value in original_env.items():
              if value is not None:
                  os.environ[key] = value
  ```

#### Database Testing
Database testing has been improved with:
- Proper mocking of database connections
- Clear separation between test and production database settings
- Environment-specific database configuration
- Mocked database operations for faster test execution
- Example:
  ```python
  @patch("module.database.init_db")
  @patch("module.config.DatabaseSettings")
  def test_database_operation(mock_settings, mock_init_db):
      # Setup mocks
      mock_settings_instance = MagicMock()
      mock_settings_instance.DATABASE_URL = "test_url"
      mock_settings.return_value = mock_settings_instance

      # Run test
      result = database_operation()

      # Verify behavior
      mock_init_db.assert_called_once_with("test_url")
  ```

7. **Assertions**
   - One logical assertion per test
   - Use descriptive assertion messages
   - Test state and behavior separately
   - Verify both positive and negative cases

### Example Test

```python
@pytest.fixture(scope="session")
def mock_component():
    """Create a reusable mock component."""
    component = Mock()
    component.process = Mock(return_value="result")
    return component

def test_component_success(mock_component):
    """Test successful component execution."""
    # Setup
    input_data = "test_input"

    # Execute
    result = mock_component.process(input_data)

    # Verify
    assert result == "result"
    mock_component.process.assert_called_once_with(input_data)
```

## Project Structure

```
src/
├── local_newsifier/
│   ├── tools/          # Tool implementations
│   │   ├── analysis/   # Analysis tools (headline trends, etc.)
│   │   └── ...         # Other tools (web scraper, NER, etc.)
│   ├── models/         # Pydantic models
│   │   └── apify.py    # Apify integration models
│   ├── flows/          # crew.ai Flow definitions
│   │   ├── analysis/   # Analysis workflows
│   │   └── ...         # Other flows (news pipeline, RSS, etc.)
│   ├── cli/            # Command Line Interface
│   │   └── commands/   # CLI command implementations
│   │       └── apify.py # Apify CLI commands
│   ├── crud/           # Database CRUD operations
│   ├── services/       # Business logic services
│   │   └── apify_service.py # Apify API integration service
│   ├── api/            # FastAPI web API
│   └── config/         # Configuration
tests/                  # Test suite
scripts/                # Runtime scripts
docs/                   # Documentation
```

## Configuration

The system can be configured through:
- Environment variables
- Configuration files in `src/local_newsifier/config/`

### Key Environment Variables

| Variable        | Description                                  | Required For                 |
|-----------------|----------------------------------------------|------------------------------|
| APIFY_TOKEN     | API token for Apify web scraping integration | Apify integration            |
| CURSOR_DB_ID    | Unique ID for cursor-specific database       | Multi-cursor support         |
| DATABASE_URL    | PostgreSQL connection string                 | Database operations          |

## Error Handling

The system implements comprehensive error handling:
- Network errors
- Parsing failures
- Processing errors
- State management issues

## State Management

Uses crew.ai's SQLite checkpointer for:
- Workflow state persistence
- Progress tracking
- Error recovery
- Flow resumption

## Monitoring

- Comprehensive logging
- State tracking
- Error reporting
- Progress monitoring

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT

## Database Configuration

### Multiple Cursor Support

The application supports running multiple cursor instances simultaneously, each with its own isolated database. This is particularly useful for development and testing.

#### How it works:
- Each cursor instance gets a unique database name based on a cursor ID
- The cursor ID is stored in the `CURSOR_DB_ID` environment variable
- If not set, a new unique ID is generated automatically

#### Setting up a new cursor instance:
1. Run the initialization script:
   ```bash
   poetry run python scripts/init_cursor_db.py
   ```
   This will:
   - Generate a unique database name for that cursor instance
   - Create a new database with that name
   - Set up all the necessary tables

2. The database name is persisted through the `CURSOR_DB_ID` environment variable, so all subsequent database operations in that cursor window will use the same database.

#### Testing with multiple cursors:
- Each cursor instance gets its own test database
- Test databases are named `test_local_newsifier_<cursor_id>`
- Tests are automatically isolated between cursor instances
