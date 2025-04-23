# Fix API System Tests

## Problem

We had two failing tests in the API system test suite:

1. `test_get_tables_api` in `tests/api/test_system.py` - The test was failing because the error response format in the API didn't include a 'name' field that the test was expecting.

2. `test_get_table_details_api` in `tests/api/test_system.py` - The test was failing because the error response didn't include expected fields when a table doesn't exist.

## Solution

1. Modified the error response format in `src/local_newsifier/api/routers/system.py` to include a 'name' field for errors, making it compatible with the test expectations.

2. Ensured dependencies required by the tests (`itsdangerous` and `python-multipart`) were properly installed.

## Changes

- Modified the error response format in `get_tables_api` function to include a 'name' field for error responses.
- Added missing dependencies to the test environment.

## Testing

All tests are now passing, with 313 tests passed and 1 skipped, and a total coverage of 89.83%, which exceeds the required 87%.

## Related Issues

These changes improve the robustness of the system by:
1. Ensuring consistent error response formats across the API
2. Maintaining backward compatibility while meeting test expectations
