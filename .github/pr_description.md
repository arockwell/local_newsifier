# Database Foundation for Local Newsifier

## Overview
This PR implements the core database foundation for the Local Newsifier project using SQLAlchemy ORM models. It provides a robust structure for storing news articles, entities, and their relationships while ensuring compatibility with the existing state model architecture.

## Key Components

### Models
- `Base` - Base SQLAlchemy model with common fields (id, created_at, updated_at)
- `Article` - Model for news articles with proper relationships to entities
- `Entity` - Model for named entities found in articles with relationship back to articles

## Implementation Features
- Comprehensive SQLAlchemy ORM models with proper relationships
- Integration with existing AnalysisStatus enum from state.py
- Normalized database structure for efficient storage
- Proper type annotations and documentation
- Support for SQLite in tests and PostgreSQL in production

## Test Coverage
The implementation includes comprehensive test coverage with unit tests for all components:
- Model validation and relationship tests with SQLite in-memory database
- Schema generation tests
- Relationship tests to ensure proper cascading behavior

## How to Use
```python
from sqlalchemy.orm import Session
from local_newsifier.models.database.article import Article
from local_newsifier.models.database.entity import Entity
from local_newsifier.models.state import AnalysisStatus

# Create a new article
article = Article(
    url="https://example.com/news/1",
    title="Local News Article",
    source_domain="example.com",
    scraped_text="This is a sample article about Gainesville.",
    status=AnalysisStatus.SCRAPE_SUCCEEDED
)

# Add entities
entity = Entity(
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

## Notes
This PR focuses on implementing the core database models as requested. Follow-up work will be needed to implement the configuration settings with Pydantic which will require addressing compatibility issues with the current Pydantic version used in the project.