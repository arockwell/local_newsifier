# Testing with Apify Integration

This document provides guidance on running tests that involve the Apify integration.

## Running Tests Without an Apify Token

Starting with version 1.x.x, the test suite is designed to run without requiring a valid Apify token. The `ApifyService` class automatically detects when it's running in a test environment and provides mock responses instead of making actual API calls.

This means:

1. You no longer need to set the `APIFY_TOKEN` environment variable to run tests
2. Tests will run faster since no actual API calls are made
3. Test results will be consistent and deterministic

## How It Works

The test mode functionality works as follows:

1. The `ApifyService` class automatically detects when it's running in a test environment (by checking for the `PYTEST_CURRENT_TEST` environment variable)
2. In test mode, if no Apify token is provided, it will use a dummy token and return mock responses
3. The mock responses are designed to mimic the structure of real Apify API responses
4. You can still provide a real token for tests if you want to test against the actual Apify API

## Mock Responses

In test mode, the following methods provide mock responses:

### `run_actor(actor_id, run_input)`

Returns a mock actor run result:

```python
{
    "id": f"test_run_{actor_id}",
    "actId": actor_id,
    "status": "SUCCEEDED",
    "defaultDatasetId": f"test_dataset_{actor_id}",
    "defaultKeyValueStoreId": f"test_store_{actor_id}",
}
```

### `get_dataset_items(dataset_id, **kwargs)`

Returns mock dataset items:

```python
{
    "items": [
        {
            "id": 1,
            "url": "https://example.com/test",
            "title": "Test Article",
            "content": "This is test content for testing without a real Apify token."
        }
    ]
}
```

### `get_actor_details(actor_id)`

Returns mock actor details:

```python
{
    "id": actor_id,
    "name": f"test_{actor_id}",
    "title": f"Test Actor: {actor_id}",
    "description": "This is a mock actor for testing without a real Apify token.",
    "version": {"versionNumber": "1.0.0"},
    "defaultRunInput": {"field1": "value1"},
}
```

## Writing Tests that Use ApifyService

When writing tests that involve `ApifyService`, you can simply instantiate the service without providing a token. The test mode will be enabled automatically:

```python
def test_some_apify_functionality():
    # No token needed, test mode is auto-detected
    service = ApifyService()

    # Will return mock data, not make a real API call
    result = service.run_actor("some_actor", {"param": "value"})

    # Assert against the mock response structure
    assert result["status"] == "SUCCEEDED"
    assert "defaultDatasetId" in result
```

If you want to explicitly set the test mode:

```python
def test_with_explicit_test_mode():
    service = ApifyService(test_mode=True)
    # ...
```

## Testing with a Real Token

If you want to test against the actual Apify API, you can still provide a real token:

```python
def test_with_real_token():
    service = ApifyService(token="your_real_token")
    # This will make actual API calls
```

Just remember to handle the case where the token might not be available in the CI environment.

## CLI Commands in Tests

CLI commands that use `ApifyService` are also automatically configured to use test mode when running tests. This allows testing the CLI commands without requiring a real token.
