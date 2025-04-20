# Local Newsifier Development Guide

## Project Overview
- News article analysis system using SQLModel, PostgreSQL, and crewai Flows
- Focuses on entity tracking, sentiment analysis, and headline trend detection
- Uses NLP for entity recognition and relationship mapping
- Supports multiple cursor instances with isolated databases

## Common Commands
- `poetry run python scripts/run_pipeline.py --url <URL>`: Process a single article
- `poetry run python scripts/demo_headline_trends.py --days 30 --interval day`: Analyze recent headlines
- `poetry run python scripts/demo_entity_tracking.py`: View entity tracking dashboard
- `poetry run python scripts/demo_sentiment_analysis.py`: Run sentiment analysis demo
- `poetry run pytest`: Run all tests
- `poetry run pytest --cov=src/local_newsifier`: Run tests with coverage
- `poetry run python -m spacy download en_core_web_lg`: Download required spaCy model

## Architecture

### Database
- Uses SQLModel (combines SQLAlchemy ORM and Pydantic validation)
- PostgreSQL backend with cursor-specific database instances
- Key models: Article, Entity, AnalysisResult, CanonicalEntity
- Database sessions should be managed with the `with_session` decorator

### Project Structure
```
src/
├── local_newsifier/
│   ├── tools/          # Tool implementations
│   │   ├── analysis/   # Analysis tools (headline trends, etc.)
│   │   └── ...         # Other tools (web scraper, NER, etc.)
│   ├── models/         # Models directory
│   │   ├── database/   # SQLModel database models
│   │   └── ...         # Other model types (state, etc.)
│   ├── flows/          # crewai Flow definitions
│   │   ├── analysis/   # Analysis workflows
│   │   └── ...         # Other flows (news pipeline, etc.)
│   ├── crud/           # Database CRUD operations
│   └── config/         # Configuration
```

## Code Style & Patterns

### Database Models
- Use SQLModel for all database models (not separate SQLAlchemy/Pydantic)
- Models are in `src/local_newsifier/models/database/`
- Example model definition:
```python
class Article(SQLModel, table=True):
    __tablename__ = "articles"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    content: str
    url: str = Field(unique=True)
    # ...
    
    entities: List["Entity"] = Relationship(back_populates="article")
```

### CRUD Operations
- CRUD operations are in `src/local_newsifier/crud/`
- Use the CRUDBase class for common operations
- Extend with model-specific operations
- Use the `with_session` decorator for session management

### Flows
- Flows are defined using crewai Flow classes
- Handle complex workflows like entity tracking and trend analysis
- Example flow usage:
```python
flow = EntityTrackingFlow()
results = flow.process_new_articles()
```

## Testing Guidelines
- Tests are organized by component type (flows, tools, models)
- Use session-scoped fixtures for expensive objects
- Mock external dependencies
- Reset mutable fixture state between tests
- Aim for >90% test coverage
- Example test structure:
```python
def test_component_success(mock_component):
    # Setup
    input_data = "test_input"
    # Execute
    result = mock_component.process(input_data)
    # Verify
    assert result == "result"
```

## Common Workflows

### Entity Tracking
1. Extract entities from article content using NER
2. Resolve entities to canonical representations
3. Track entity mentions across articles
4. Analyze entity relationships and co-occurrences

### Headline Analysis
1. Extract keywords from headlines
2. Track keyword frequency over time
3. Detect trends and generate reports
4. Output in various formats (markdown, JSON)

### Sentiment Analysis
1. Identify entity mentions in context
2. Score sentiment of surrounding text
3. Aggregate sentiment scores over time
4. Track sentiment trends for entities

## Database Configuration

### Multiple Cursor Support
- Each cursor instance gets a unique database
- Database name based on cursor ID in `CURSOR_DB_ID` environment variable
- Initialize with `scripts/init_cursor_db.py`
- Test databases are named `test_local_newsifier_<cursor_id>`

## Known Issues & Gotchas
- Environment variables must be properly managed in tests
- Database connections should be properly closed to avoid connection pool issues
- Type hints may need `TYPE_CHECKING` imports to avoid circular references
- SQLModel combines SQLAlchemy and Pydantic - use model_dump() not dict()
