# Apify Error Handling Guide

This document describes the error handling patterns implemented for the Apify integration in Local Newsifier.

## Error Types

The Apify integration uses a hierarchy of error types to provide context-rich error handling:

### `ApifyError`

Base class for all Apify-related errors with the following features:
- Preserves the original exception
- Captures operation context
- Provides error codes based on HTTP status codes
- Structured logging with detailed context
- Consistent formatting for user-facing messages

### Specific Error Types

| Error Type | Description | Typical Use Cases |
|------------|-------------|-------------------|
| `ApifyAuthError` | Authentication or authorization issues | Invalid tokens, expired tokens, insufficient permissions |
| `ApifyRateLimitError` | API rate limit exceeded | Too many requests in a time period |
| `ApifyNetworkError` | Network connectivity issues | Connection timeouts, DNS failures |
| `ApifyAPIError` | General API errors | Base class for specific API errors |
| `ApifyActorError` | Actor-specific errors | Invalid actor ID, actor execution failures |
| `ApifyDatasetError` | Dataset-specific errors | Invalid dataset ID, dataset access issues |
| `ApifyDataProcessingError` | Data transformation issues | JSON parsing errors, unexpected data formats |

## Using Error Handling

### Decorators

Three decorators are available for handling Apify-related errors:

#### 1. `with_apify_error_handling`

Transforms exceptions into appropriate ApifyError types:

```python
@with_apify_error_handling(operation_name="custom_operation", include_args=True)
def my_function(param1, param2):
    # Function that may raise errors
    pass
```

#### 2. `with_apify_retry`

Adds retry logic for transient errors:

```python
@with_apify_retry(
    max_attempts=3,
    min_wait=1.0,
    max_wait=10.0,
    retry_network_errors=True,
    retry_rate_limit_errors=True
)
def my_function():
    # Function that may experience transient failures
    pass
```

#### 3. `with_apify_timing`

Logs execution time for performance analysis:

```python
@with_apify_timing(operation_name="my_operation", log_level=logging.INFO)
def my_function():
    # Function to be timed
    pass
```

#### Combined Decorator

For convenience, a combined decorator applies all three:

```python
@apply_full_apify_handling(
    operation_name="my_operation",
    max_attempts=3,
    retry_network_errors=True,
    retry_rate_limit_errors=True
)
def my_function():
    # Function with complete error handling
    pass
```

### CLI Error Handling

The CLI commands use the `handle_apify_error` function to provide user-friendly error messages:

```python
try:
    # Call Apify service
    result = apify_service.run_actor(actor_id, run_input)
except Exception as e:
    return handle_apify_error(e)
```

This produces color-coded, context-aware error messages with appropriate exit codes.

## Error Handling Flow

1. **Error Detection**: A function decorated with error handling raises an exception
2. **Error Transformation**: The exception is transformed into an appropriate ApifyError
3. **Context Preservation**: Operation context is captured and preserved
4. **Logging**: The error is logged with full context
5. **Retry Attempt**: For transient errors with retry enabled, retries are attempted
6. **User Feedback**: User-friendly error message is displayed (CLI) or returned (API)

## Best Practices

### 1. Use Appropriate Error Types

Match error types to specific error conditions:

```python
if not token:
    raise ApifyAuthError("API token not provided")
```

### 2. Include Context

Provide useful context with errors:

```python
raise ApifyActorError(
    message="Failed to run actor",
    operation="run_actor",
    context={"actor_id": actor_id},
    original_error=error
)
```

### 3. Apply Consistent Decorators

Use decorators consistently on all Apify-related methods:

```python
@apply_full_apify_handling(operation_name="my_service.my_method")
def my_method(self, param1, param2):
    # Implementation
```

### 4. Handle Errors Appropriately

Check for specific error types when needed:

```python
try:
    result = apify_service.run_actor(actor_id, run_input)
except ApifyRateLimitError as e:
    # Handle rate limit specifically
    retry_after = e.retry_after or 60
    time.sleep(retry_after)
    # Try again
except ApifyAuthError:
    # Handle auth errors specifically
    # Prompt for new token
except ApifyError as e:
    # Handle all other Apify errors
```

## Integration with Fastapi-Injectable

The error handling components are designed to be compatible with fastapi-injectable:

```python
@injectable
class InjectableApifyService:
    def __init__(
        self,
        token: Annotated[Optional[str], Depends(get_apify_token)]
    ):
        self._token = token
        self._client = None
    
    @apply_full_apify_handling(operation_name="apify.run_actor")
    def run_actor(self, actor_id: str, run_input: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation
```