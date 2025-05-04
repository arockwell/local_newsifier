# Complete fastapi-injectable provider implementations

## Summary
This issue tracks the completion of the fastapi-injectable provider implementations to ensure consistent DI usage.

## Background
We are migrating from our custom DIContainer to fastapi-injectable as documented in issue #142, but there are still several tools and services that need proper provider implementations.

## Tools Added in The Current PR
- SentimentAnalyzer provider (get_sentiment_analyzer_tool)
- SentimentTracker provider (get_sentiment_tracker_tool)
- TrendAnalyzer provider (get_trend_analyzer_tool)
- TrendReporter provider (get_trend_reporter_tool)
- ContextAnalyzer provider (get_context_analyzer_tool)
- Added missing aliases with _tool suffix for consistent naming pattern

## Tools/Services Still Needing Providers
1. EntityTracker - Add get_entity_tracker_tool provider
2. OpinionVisualizer - Add get_opinion_visualizer_tool provider 
3. FileWriter - Add get_file_writer_tool provider
4. Flow classes:
   - Need injectable versions of NewsPipelineFlow, EntityTrackingFlow, and PublicOpinionFlow
   - Update TrendAnalysisFlow to accept dependencies via DI rather than direct instantiation

## Acceptance Criteria
- All analysis and extraction tools have consistent provider implementations
- All tools have _tool suffix versions for backwards compatibility
- Provider functions use appropriate caching strategy (use_cache=False for most tools)
- Documentation is updated if needed to reflect new providers
- Tests are updated to use the new providers

## Implementation Details
- Ensure consistent docstrings across all provider functions
- Maintain the same pattern for naming and implementation
- Ensure proper error handling if tool initialization fails