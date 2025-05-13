You'll analyze test failures to help debug and fix failing tests.

If a test file path is provided (e.g., project:analyze_test_failures tests/services/test_entity_service.py):
- Focus analysis on that specific test file
- Run the test with verbose output to understand failures

If no test file is provided:
- Show a list of recently failing tests from pytest reports if available
- Provide guidance on how to specify a test file

Analyze the test failure with these steps:

1. Run the specified test with verbose output and collect error details:
   python -m pytest {test_file} -v

2. If the test fails, examine the error details:
   - Error type and message
   - Test function and assertion that failed
   - Line numbers for the failure

3. Check the commit history for recent changes affecting this test:
   git log -p -- {test_file} --since="2 weeks ago"
   
   Also check related implementation files:
   git log -p -- {related_implementation_file} --since="2 weeks ago"

4. Look for common failure patterns:
   - Missing dependencies or imports
   - Uninitialized variables or attributes
   - Assertion errors (expected vs. actual values)
   - Mocking issues
   - Event loop or async problems
   - Database connection issues

5. Suggest potential fixes based on the error pattern:
   - For import errors: Check for missing or incorrect imports
   - For attribute errors: Check for initialization order or missing setup
   - For assertion errors: Compare expected vs. actual values
   - For timeout errors: Check for infinite loops or blocking calls
   - For event loop errors: Check for proper async/await usage

6. Verify dependencies and mocks used in the test:
   - Check if the correct fixtures are being used
   - Look for mock setup issues
   - Verify test isolation (tests affecting each other)

This deep analysis helps you understand why tests are failing and provides actionable steps to fix them.