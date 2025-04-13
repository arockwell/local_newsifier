# Description

This PR improves the database foundation of the project by enhancing the models, configuration, and test coverage.

# Changes

- Enhanced database manager with better type safety and error handling
- Updated database model imports and exports
- Improved configuration settings for database connections
- Added support for environment-specific database configurations
- Added comprehensive test suite for database models
- Enhanced test configuration and fixtures

# Testing

- Added extensive test coverage for:
  - Settings configuration
  - Base model functionality
  - Article and entity models
  - Database integration tests
- All tests are passing in the development environment

# Notes

This PR establishes a solid foundation for our database layer with proper testing and configuration management.

---

# Checklist
* [x] Tests added/updated and passing
* [x] Documentation updated (if needed)
* [x] Code follows project style guidelines
* [x] Verified changes in development environment

# Database Foundation for Local Newsifier

## Overview
This PR implements the core database foundation for the Local Newsifier project using SQLAlchemy ORM models. It provides a robust structure for storing news articles, entities, and their relationships while ensuring full compatibility with the existing codebase.

## Key Components

### Models
- `Base` - Base SQLAlchemy model with common fields (id, created_at, updated_at)
- `ArticleDB` - Model for news articles with proper relationships to entities
- `EntityDB` - Model for named entities found in articles with relationship back to articles
- `AnalysisResultDB` - Model for storing analysis results with relationship to articles

## Implementation Features
- Comprehensive SQLAlchemy ORM models with proper relationships
- Integration with existing AnalysisStatus enum from state.py
- Normalized database structure for efficient storage
- Complete backward compatibility with existing Pydantic models
- Proper field validation with appropriate constraints and indexes
- Enhanced PostgreSQL support with proper data types
- Cascading relationships for effective data management

## Test Coverage
The implementation includes comprehensive test coverage with real PostgreSQL tests:
- Model validation and relationship tests with actual PostgreSQL database
- Schema generation tests to ensure proper table creation
- Relationship tests to ensure proper cascading behavior
- Compatibility tests with existing Pydantic models

## How to Use
```python
from sqlalchemy.orm import Session
from local_newsifier.models.database import ArticleDB, EntityDB, AnalysisResultDB
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

# Save to database
with Session() as session:
    session.add(article)
    session.commit()
```