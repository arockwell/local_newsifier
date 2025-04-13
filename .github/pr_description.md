# Sentiment Analysis and Public Opinion Tracking

## Summary

This PR adds a complete sentiment analysis and public opinion tracking feature to the local newsifier system. The implementation allows analyzing the emotional tone of news articles, tracking sentiment changes over time, detecting significant opinion shifts, and generating both single-topic and comparative reports.

## Changes

- Added new database models for sentiment analysis, opinion trends, and sentiment shifts in `models/sentiment.py`
- Implemented a lexicon-based sentiment analyzer in `tools/sentiment_analyzer.py`
- Created a sentiment tracking system in `tools/sentiment_tracker.py` for monitoring trends over time
- Added visualization and reporting capabilities in `tools/opinion_visualizer.py`
- Implemented the main flow orchestration in `flows/public_opinion_flow.py`
- Added comprehensive test coverage for all components
- Created a demonstration script to showcase the new features

## Testing

- Implemented unit tests for all components with > 90% code coverage
- Tests include edge cases like empty data, error conditions, and correlation analysis
- Included a demonstration script that can be run against a local database to showcase features

## Implementation Details

### Sentiment Analysis

The implementation uses a lexicon-based approach for sentiment analysis, which provides good performance without requiring external API calls or dependencies. Key features include:

- Document-level and sentence-level sentiment scoring
- Entity-specific sentiment extraction
- Topic-based sentiment analysis
- Handling of negation and intensifiers in text

### Opinion Tracking

The system can track sentiment over time and detect significant shifts:

- Supports different time intervals (day, week, month)
- Calculates sentiment distributions and trends
- Detects statistically significant shifts in public opinion
- Correlates sentiment across different topics

### Visualization and Reporting

Reports can be generated in various formats:

- Plain text for CLI usage
- Markdown for documentation
- HTML for web display

Reports include sentiment timelines, comparative analyses, and confidence intervals.

### Integration

The feature integrates with the existing pipeline and database structure:

- Uses the existing database manager
- Extends the analysis results model
- Integrates with the entity tracking system
- Follows the established flow pattern