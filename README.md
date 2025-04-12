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
- Robust error handling and retry mechanisms
- State persistence and workflow resumption
- Comprehensive logging and monitoring

## Setup

1. Install Poetry (package manager):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Install dependencies:
```bash
poetry install
```

3. Download spaCy model:
```bash
poetry run python -m spacy download en_core_web_lg
```

## Usage

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
│   ├── flows/          # crew.ai Flow definitions
│   │   ├── analysis/   # Analysis workflows
│   │   └── ...         # Other flows (news pipeline, RSS, etc.)
│   └── config/         # Configuration
tests/                  # Test suite
scripts/                # Runtime scripts
```

## Configuration

The system can be configured through:
- Environment variables
- Configuration files in `src/local_newsifier/config/`

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
