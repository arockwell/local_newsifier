# Mock APIFY_TOKEN in Tests

## Issue Description
When running the full test suite, the tests fail with the error "Error: APIFY_TOKEN is not set." This is preventing the full test suite from passing, even though many of the individual tests pass when run in isolation.

## Expected Behavior
Tests should run successfully without requiring the APIFY_TOKEN environment variable to be set, by properly mocking the Apify service or using sensible defaults in test mode.

## Current Behavior
Tests fail because they're trying to use the real Apify service which requires a token, even in test environment.

## Steps to Reproduce
1. Run the full test suite with `poetry run pytest`
2. Observe the error "Error: APIFY_TOKEN is not set"

## Proposed Solution
1. Update the tests to mock the Apify service and avoid making real API calls
2. Add a fixture to the test configuration that provides a mock APIFY_TOKEN when tests run
3. Update the Apify client initialization to use a dummy token in test environments
4. Add clear documentation about how to properly test Apify-related functionality

## Affected Files
- `src/local_newsifier/services/apify_service.py`
- `tests/services/test_apify_service.py`
- `tests/services/test_apify_service_extended.py`
- Other tests that indirectly use the Apify service

## Additional Context
- This is impacting the ability to run the full test suite and making CI builds fail
- We should follow the same pattern we used for mocking database connections in tests