# Local Newsifier Development Guide

## Project Overview
- News article analysis system using SQLModel, PostgreSQL, and dependency injection
- Focuses on entity tracking, sentiment analysis, and headline trend detection
- Uses NLP for entity recognition and relationship mapping
- Supports multiple content acquisition methods (RSS feeds, Apify web scraping)
- Uses Celery with Redis for asynchronous task processing
- Deployed on Railway with web, worker, and scheduler processes

## Common Commands
- `nf help`: Show available commands and options
- `nf run-pipeline --url <URL>`: Process a single article
- `nf demo-headline-trends --days 30 --interval day`: Analyze recent headlines
- `nf demo-entity-tracking`: View entity tracking dashboard
- `nf demo-sentiment-analysis`: Run sentiment analysis demo
- `nf feeds list`: List configured RSS feeds
- `nf feeds fetch`: Fetch articles from feeds
- `nf apify test`: Test Apify API connection
- `nf apify scrape-content <URL>`: Scrape content using Apify
- `poetry run pytest`: Run all tests
- `poetry run pytest --cov=src/local_newsifier`: Run tests with coverage
- `poetry run python -m spacy download en_core_web_lg`: Download required spaCy model

## Architecture

### Database
- Uses SQLModel (combines SQLAlchemy ORM and Pydantic validation)
- PostgreSQL backend with cursor-specific database instances
- Key models: Article, Entity, AnalysisResult, CanonicalEntity, ApifySourceConfig, RSSFeed
- Database sessions should be managed with the `with_session` decorator

### Project Structure
```
src/
├── local_newsifier/
│   ├── api/            # FastAPI web interface
│   │   ├── routers/    # API endpoint definitions
│   │   └── templates/  # Jinja2 templates for web UI
│   ├── cli/            # Command-line interface
│   │   └── commands/   # CLI command implementations
│   ├── config/         # Configuration settings
│   ├── container.py    # Dependency injection container
│   ├── crud/           # Database CRUD operations
│   ├── database/       # Database connection and session management
│   ├── flows/          # High-level workflow definitions
│   │   └── analysis/   # Analysis workflows
│   ├── models/         # Data models
│   │   └── apify.py    # Apify integration models
│   ├── services/       # Business logic services
│   │   └── apify_service.py  # Apify API integration
│   ├── tasks.py        # Celery tasks
│   └── tools/          # Processing tools
│       ├── analysis/   # Analysis tools
│       ├── extraction/ # Entity extraction tools
│       └── resolution/ # Entity resolution tools
```

## Code Style & Patterns

### Database Models
- Use SQLModel for all database models (not separate SQLAlchemy/Pydantic)
- Models are in `src/local_newsifier/models/`
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

### Dependency Injection
- The system uses a central DIContainer for managing dependencies
- Components should be registered with the container
- Services get dependencies through the container
- This helps prevent circular imports and improves testability
- Example container usage:
```python
# Get a service from the container
article_service = container.get("article_service")

# Register a service with the container
container.register_factory("article_service", lambda c: ArticleService(
    article_crud=c.get("article_crud"),
    session_factory=c.get("session_factory")
))
```

### Service Layer
- Services coordinate business logic between CRUD operations and tools
- Services are in `src/local_newsifier/services/`
- Example service method:
```python
def analyze_headline_trends(self, start_date, end_date, time_interval="day"):
    with self.session_factory() as session:
        articles = self.article_crud.get_by_date_range(
            session, start_date, end_date
        )
        
        trend_analyzer = self.container.get("trend_analyzer_tool")
        results = trend_analyzer.extract_keywords([a.title for a in articles])
        
        return {"trending_terms": results}
```

### Integration Services
- External API integrations use dedicated service classes
- The ApifyService encapsulates all Apify API interactions
- Example integration service:
```python
class ApifyService:
    def __init__(self, token=None):
        self._token = token
        self._client = None
        
    def run_actor(self, actor_id, run_input):
        return self.client.actor(actor_id).call(run_input=run_input)
```

### Session Management
- Use context managers for database sessions:
```python
with SessionManager() as session:
    # Database operations here
    # Session is committed on exit, or rolled back on exception
```

- For service methods:
```python
with self.session_factory() as session:
    # Use session for database operations
```

- Avoid carrying SQLModel objects between sessions to prevent "Instance is not bound to a Session" errors

### Best Practices
- Return IDs rather than SQLModel objects across session boundaries
- Use lazy loading with the container for circular dependencies
- Bind parameters to SQLModel queries before execution:
```python
# Correct way to bind parameters in SQLModel
query = query.bindparams(param=value)
results = session.exec(query).all()
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

### Content Acquisition
1. **RSS Feed Processing**:
   - Configure RSS feeds in the database
   - Fetch and parse feed entries
   - Create articles from feed entries
   - Process articles for entities and analysis

2. **Apify Web Scraping**:
   - Configure scraping sources
   - Run Apify actors to scrape content
   - Store raw data in the database
   - Transform data into articles for processing

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

## Database Configuration

### Multiple Cursor Support
- Each cursor instance gets a unique database
- Database name based on cursor ID in `CURSOR_DB_ID` environment variable
- Initialize with `scripts/init_cursor_db.py`
- Test databases are named `test_local_newsifier_<cursor_id>`

## Deployment

### Railway Configuration
- Railway.json configures multiple processes:
  - web: FastAPI web interface
  - worker: Celery worker for task processing
  - beat: Celery beat for scheduled tasks
- Required environment variables:
  - POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB
  - CELERY_BROKER_URL (Redis URL for Celery broker)
  - CELERY_RESULT_BACKEND (Redis URL for Celery results)
  - APIFY_TOKEN (for Apify web scraping)

## Known Issues & Gotchas
- Environment variables must be properly managed in tests
- Database connections should be properly closed to avoid connection pool issues
- Type hints may need `TYPE_CHECKING` imports to avoid circular references
- SQLModel combines SQLAlchemy and Pydantic - use model_dump() not dict()
- SQLModel.exec() only takes one parameter - bind params to the query before calling
- Avoid passing SQLModel objects between sessions - use IDs instead
- Use runtime imports to break circular dependencies
- Redis is required for Celery - PostgreSQL is no longer supported as a broker