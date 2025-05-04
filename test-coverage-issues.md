# Test Coverage Issues for fastapi-injectable Migration

This document outlines the test coverage gaps identified in PR #154 that implements the fastapi-injectable migration foundation. These issues should be addressed in follow-up PRs to maintain code quality and reliability.

## Issue 1: ContainerAdapter Test Coverage

**Component**: `src/local_newsifier/fastapi_injectable_adapter.py::ContainerAdapter`

**Current Coverage**: ~40%

**Target Coverage**: 85%

**Coverage Gaps**:

- `get_service()` method - Missing tests for:
  - Type-based service lookup
  - Factory-based service creation path
  - Error handling paths

**Proposed Solutions**:

- Fix existing tests that are failing with `InvalidSpecError`
- Replace `MagicMock(spec=service_class)` with `MagicMock()` and explicit type checks
- Add dedicated test cases for each lookup path in the method

**Priority Level**: High (Core functionality of the adapter)

## Issue 2: Async Functions Test Coverage

**Component**: `src/local_newsifier/fastapi_injectable_adapter.py` - Async Functions

**Current Coverage**: ~30% 

**Target Coverage**: 80%

**Coverage Gaps**:

- `migrate_container_services()` - Lack of coverage for:
  - Service registration logic
  - Error handling in nested loops
  - Integration with FastAPI application
- `lifespan_with_injectable()` - Missing tests for:
  - Startup and shutdown hooks
  - Error handling during initialization

**Proposed Solutions**:

- Create dedicated async test fixtures
- Use pytest-asyncio for proper async test support
- Add test cases for successful registration and error scenarios
- Create mock FastAPI app for integration testing

**Priority Level**: Medium (Important for application initialization)

## Issue 3: Error Handling Path Coverage

**Component**: Multiple functions in `fastapi_injectable_adapter.py`

**Current Coverage**: ~20% for error paths

**Target Coverage**: 75%

**Coverage Gaps**:

- Exception handlers in `register_container_service()` - Lines 213-221
- Error logging in `migrate_container_services()` - Lines 280-304
- Various try/except blocks throughout the code

**Proposed Solutions**:

- Create test scenarios that force specific exceptions
- Add test cases that verify log messages are correctly issued
- Ensure each exception type is tested separately

**Priority Level**: Medium (Critical for production reliability)

## Issue 4: Integration with FastAPI

**Component**: Integration between adapter and FastAPI application

**Current Coverage**: ~50%

**Target Coverage**: 85%

**Coverage Gaps**:

- Skipped tests in `tests/api/test_main.py` related to lifespan
- Integration of adapter within actual FastAPI request context
- End-to-end DI resolution chain with both systems

**Proposed Solutions**:

- Un-skip the tests in `test_main.py` and update for new patterns
- Add integration tests for full request lifecycle
- Test realistic service resolution scenarios

**Priority Level**: Medium (Important for ensuring working web API)

## Implementation Plan

1. Address Issue 1 (Container Adapter) first as this will enable other tests
2. Address Issues 2 & 3 (Async & Error handling) in parallel
3. Address Issue 4 (Integration tests) last

Expected timeline: Complete all issues within 2 weeks of PR #154 being merged.