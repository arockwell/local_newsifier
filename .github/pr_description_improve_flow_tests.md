# Improve Flow Module Test Coverage

## Summary
This PR improves the test coverage of the flow modules by fixing failing tests and adding new tests for previously untested code paths. The overall flow module test coverage has increased to 81%.

## Changes
- Fixed failing tests in `tests/flows/analysis/test_headline_trend_flow.py`
- Fixed failing tests in `tests/flows/test_trend_analysis_flow.py`
- Enhanced test coverage for `entity_tracking_flow_service.py` with comprehensive test cases
- Improved error handling test coverage across all modules
- Changed the approach for testing decorated methods, particularly those using `@with_session`

## Test Coverage Improvements
- `headline_trend_flow.py`: 100% (86/86 statements)
- `trend_analysis_flow.py`: 92% (96/104 statements)
- `entity_tracking_flow_service.py`: 100% (23/23 statements)
- Overall flow module coverage: 81% (455/559 statements)

## Remaining Issues
- `entity_tracking_flow.py` has 0% test coverage (84 statements)
  - Used only in demo scripts
  - Duplicates some functionality with `entity_tracking_flow_service.py`
  - Would require significant refactoring to properly test
- Minor coverage gaps in `news_pipeline.py` (4 statements), `public_opinion_flow.py` (8 statements), and `trend_analysis_flow.py` (8 statements)

## Technical Notes
1. For methods decorated with `@with_session`, testing is complicated by the decorator injecting new sessions. We're now using a more direct approach by patching the decorated method or the decorator itself.
2. Exception handling was improved by directly creating error states or patching methods to simulate specific errors.
3. Used a more focused approach to test database-dependent code by mocking at the right level of abstraction.

## Future Work
- Consider consolidating the duplicate entity tracking implementations
- Address the remaining minor coverage gaps in other flow modules
- Improve the session handling in tests to make them more robust
