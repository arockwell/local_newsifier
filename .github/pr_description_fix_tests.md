# Fix Test Failures and Remove NER Analyzer Tool

## Problem

We had two failing tests in the test suite:

1. `test_pipeline_analysis_failure` in `tests/flows/test_news_pipeline.py` - The test was failing because the error handling in the pipeline was not properly catching the exception from the article service.

2. `test_entity_processing_integration` in `tests/integration/test_entity_processing.py` - The test was failing because no entities were being extracted from the test article due to session management issues.

Additionally, the NER analyzer tool was deprecated and needed to be removed.

## Solution

1. Fixed error handling in `NewsPipelineFlow.process_content` to properly handle exceptions without re-raising them, allowing the flow to continue with the error state.

2. Fixed session management in `EntityService.process_article_entities` to use the provided session_factory instead of creating a new SessionManager directly, ensuring that the custom session factory provided in tests is used.

3. Removed the deprecated NER analyzer tool and its tests.

4. Updated memory bank documentation to reflect these changes.

## Changes

- Modified `NewsPipelineFlow.process_content` to not re-raise exceptions after setting the error state
- Modified `EntityService.process_article_entities` to use `self.session_factory()` instead of `SessionManager()`
- Removed `src/local_newsifier/tools/ner_analyzer.py` and `tests/tools/test_ner_analyzer.py`
- Updated memory bank documentation in `activeContext.md` and `progress.md`

## Testing

All tests are now passing (308 tests), confirming that our fixes resolved the issues.

## Related Issues

These changes improve the robustness of the system by:
1. Ensuring proper error handling in the pipeline
2. Fixing session management to work correctly with custom session factories
3. Removing deprecated code to reduce maintenance burden
