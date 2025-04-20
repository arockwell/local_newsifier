# Remove Duplicated Tools

## Problem

After implementing the service layer and refactoring the tools to use it, we ended up with several duplicated tools in the codebase:

1. `src/local_newsifier/tools/context_analyzer.py` and `src/local_newsifier/tools/analysis/context_analyzer.py`
2. `src/local_newsifier/tools/entity_resolver.py` and `src/local_newsifier/tools/resolution/entity_resolver.py`
3. `src/local_newsifier/tools/entity_tracker.py` and `src/local_newsifier/tools/entity_tracker_service.py`

These duplications made it unclear which implementation should be used and increased the maintenance burden.

## Solution

1. Removed the older, duplicated tools:
   - `src/local_newsifier/tools/context_analyzer.py`
   - `src/local_newsifier/tools/entity_resolver.py`
   - `src/local_newsifier/tools/entity_tracker.py`

2. Updated references to use the newer implementations:
   - Updated `src/local_newsifier/flows/entity_tracking_flow.py` to use `entity_tracker_service.py`
   - Updated `tests/flows/entity_tracking_flow_test.py` to use `entity_tracker_service.py`
   - Modified `find_entity_relationships` method in `entity_tracking_flow.py` to use `canonical_entity_crud` directly

3. Removed the associated test files:
   - `tests/tools/test_context_analyzer.py`
   - `tests/tools/entity_resolver_test.py`
   - `tests/tools/test_entity_tracker.py`

## Changes

- Removed 3 duplicated tool implementations
- Removed 3 associated test files
- Updated references to use the newer implementations
- Fixed the `find_entity_relationships` method to work with the new architecture

## Testing

All 291 tests are passing, confirming that our changes did not break any functionality.

## Related Issues

This PR continues the refactoring work to implement the hybrid architecture with improved tool APIs, CRUD modules, and a service layer. It aligns with the project's goal of having a cleaner, more maintainable codebase with clear separation of concerns.
