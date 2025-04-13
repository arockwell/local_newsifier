# Add News Investigation Crew

## Summary
This PR adds a new `NewsInvestigationCrew` class that leverages crewai to conduct self-directed investigations into local news data. The feature enables finding connections between entities in news articles and generating investigation reports.

## Features Added
- `NewsInvestigationCrew` class with methodology for investigating relationships between entities in news
- Support for both self-directed and topic-focused investigations
- Report generation in multiple formats (Markdown, HTML)
- Enhanced `FileWriter` class with improved file writing capabilities
- Integration with existing entity tracking and context analysis tools

## Technical Details
- Built on crewai framework with researcher, analyst, and reporter agents
- Supporting entity connection model
- Comprehensive test suite with >99% code coverage
- Non-destructive implementation that builds on existing entity tracking system

## Testing
- Test coverage for crews module: 99%
- Overall project test coverage: 92%
- All tests passing

## Future Improvements
- PDF report generation
- Visualization of entity connections
- Persistence of investigation results in database
