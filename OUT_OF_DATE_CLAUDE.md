# Out of Date CLAUDE.md Files

This document identifies CLAUDE.md files that contain outdated information based on the current implementation status of Local Newsifier.

## Summary

The project has undergone significant architectural changes, particularly:
1. Complete migration from custom DI container to fastapi-injectable
2. Introduction of async patterns and async database sessions
3. Removal of legacy session utilities
4. Changes in dependency injection patterns and provider functions

## Files Requiring Updates

### 1. `/src/local_newsifier/database/CLAUDE.md`

**Issues:**
- Line 13: States "Legacy `session_utils.py` module has been removed" but doesn't mention the new async capabilities
- Missing documentation about `async_engine.py` and async session management
- No mention of the async providers in `di/async_providers.py`
- Should document the dual sync/async database access patterns now available

**Recommended Updates:**
- Add section on async database patterns
- Document `get_async_session()` usage
- Explain when to use sync vs async sessions
- Update examples to show both patterns

### 2. `/src/local_newsifier/di/CLAUDE.md`

**Issues:**
- Lines 26-50: Mentions three scopes (SINGLETON, TRANSIENT, REQUEST) but fastapi-injectable doesn't use these scope names
- The actual implementation uses `use_cache=True/False` parameter, not scope enums
- Missing documentation about async providers in `async_providers.py`
- Doesn't mention that the project standardized on `use_cache=False` for all providers

**Recommended Updates:**
- Replace scope discussion with `use_cache` parameter explanation
- Add section on async providers
- Update examples to reflect current implementation
- Document the project's decision to use `use_cache=False` everywhere

### 3. `/src/local_newsifier/services/CLAUDE.md`

**Issues:**
- Missing documentation about async services (e.g., `apify_service_async.py`, `apify_webhook_service_async.py`)
- Session management examples don't show async patterns
- Injectable service pattern section doesn't mention async service capabilities

**Recommended Updates:**
- Add section on async services
- Document the async webhook handling
- Show examples of async service methods
- Explain when to use sync vs async services

### 4. `/src/local_newsifier/crud/CLAUDE.md`

**Issues:**
- No mention of async CRUD operations (`async_base.py`, `async_article.py`)
- Examples only show sync patterns
- Missing guidance on when to use async CRUD vs sync CRUD

**Recommended Updates:**
- Add section on async CRUD patterns
- Document the AsyncCRUDBase class
- Show examples of async CRUD operations
- Explain the differences between sync and async CRUD

### 5. `/src/local_newsifier/api/CLAUDE.md`

**Issues:**
- Line 27: Shows old container-based dependency injection pattern
- Lines 130-187: Injectable endpoints section doesn't reflect that ALL endpoints now use injectable
- Missing documentation about async endpoint patterns
- No mention of the async webhook endpoint implementation

**Recommended Updates:**
- Remove references to old DI container
- Update all examples to use current injectable patterns
- Add section on async endpoints
- Document the webhook async handling

### 6. `/src/local_newsifier/cli/CLAUDE.md`

**Issues:**
- Lines 62-74: Service access section shows old provider pattern
- No mention that CLI might need to handle async operations
- Examples don't reflect current injectable patterns

**Recommended Updates:**
- Update service access examples to current patterns
- Add notes about handling async operations in CLI
- Update import statements in examples

### 7. `/tests/CLAUDE.md`

**Issues:**
- Lines 74-84: Async testing section mentions centralized event loop fixture, but recent fixes removed flaky decorators
- Missing information about testing async CRUD and services
- No mention of async webhook testing patterns

**Recommended Updates:**
- Update async testing guidance based on recent event loop stabilization
- Add examples for testing async CRUD operations
- Document async service testing patterns
- Remove references to deprecated CI skip decorators

### 8. `/tests/api/CLAUDE.md`

**Issues:**
- Examples don't show async endpoint testing with new async services
- Missing webhook async testing patterns
- No examples of testing with async database sessions

**Recommended Updates:**
- Add async endpoint testing examples
- Document webhook testing with async patterns
- Show how to mock async dependencies

### 9. `/tests/services/CLAUDE.md`

**Issues:**
- No documentation for testing async services
- Missing examples for async webhook service testing
- AsyncMock usage examples are limited

**Recommended Updates:**
- Add comprehensive async service testing section
- Document testing patterns for async database operations
- Show examples of testing async webhook handlers

## Priority Updates

1. **High Priority**: Update DI-related documentation (di/CLAUDE.md, services/CLAUDE.md) to reflect fastapi-injectable patterns
2. **High Priority**: Add async documentation to database, CRUD, and service guides
3. **Medium Priority**: Update testing guides with async patterns
4. **Medium Priority**: Update API documentation to remove old DI references
5. **Low Priority**: Update CLI documentation for current patterns

## Next Steps

1. Update each CLAUDE.md file to reflect current implementation
2. Add new sections for async patterns where applicable
3. Remove all references to the old DI container
4. Ensure all code examples use current patterns
5. Add cross-references between sync and async documentation
