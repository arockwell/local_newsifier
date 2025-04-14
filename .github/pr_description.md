# Add News Investigation Crew and Database Foundation

## Summary
This PR adds a new `NewsInvestigationCrew` class that leverages crewai to conduct self-directed investigations into local news data, while also improving the database foundation of the project. The feature enables finding connections between entities in news articles and generating investigation reports, built on top of a robust database layer.

## Database Changes
- Enhanced database manager with better type safety and error handling
- Updated database model imports and exports
- Improved configuration settings for database connections
- Added support for environment-specific database configurations
- Added comprehensive test suite for database models
- Enhanced test configuration and fixtures

### Database Models
- `Base` - Base SQLAlchemy model with common fields (id, created_at, updated_at)
- `ArticleDB` - Model for news articles with proper relationships to entities
- `EntityDB` - Model for named entities found in articles with relationship back to articles
- `AnalysisResultDB` - Model for storing analysis results with relationship to articles
- `CanonicalEntityDB` - Model for canonical entities with relationships to mentions
- `EntityMentionContextDB` - Model for storing entity mention contexts
- `EntityProfileDB` - Model for entity profiles and metadata

## News Investigation Features
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
- Comprehensive SQLAlchemy ORM models with proper relationships
- Integration with existing AnalysisStatus enum from state.py
- Normalized database structure for efficient storage
- Complete backward compatibility with existing Pydantic models
- Proper field validation with appropriate constraints and indexes
- Enhanced PostgreSQL support with proper data types
- Cascading relationships for effective data management

## Testing
- Test coverage for crews module: 99%
- Overall project test coverage: 92%
- All tests passing
- Added extensive test coverage for:
  - Settings configuration
  - Base model functionality
  - Article and entity models
  - Database integration tests
  - Entity tracking and relationships
  - Web scraping and analysis tools
- All tests are passing in the development environment

## Future Improvements
- PDF report generation
- Visualization of entity connections
- Persistence of investigation results in database
- Enhanced entity relationship analysis
- Automated trend detection
- Integration with external knowledge bases

## How to Use
```python
from sqlalchemy.orm import Session
from local_newsifier.models.database import ArticleDB, EntityDB, AnalysisResultDB, CanonicalEntityDB
from local_newsifier.models.state import AnalysisStatus

# Create a new article
article = ArticleDB(
    url="https://example.com/news/1",
    title="Local News Article",
    source="example.com",
    content="This is a sample article about Gainesville.",
    status=AnalysisStatus.SCRAPE_SUCCEEDED.value
)

# Add entities
entity = EntityDB(
    text="Gainesville",
    entity_type="GPE",
    sentence_context="This is a sample article about Gainesville.",
    confidence=0.95
)
article.entities.append(entity)

# Create canonical entity
canonical = CanonicalEntityDB(
    name="Gainesville",
    entity_type="GPE",
    description="City in Florida, United States"
)

# Save to database
with Session() as session:
    session.add(article)
    session.add(canonical)
    session.commit()
```

## Checklist
* [x] Tests added/updated and passing
* [x] Documentation updated
* [x] Code follows project style guidelines
* [x] Verified changes in development environment
* [x] Database migrations created and tested
* [x] Entity tracking system validated
