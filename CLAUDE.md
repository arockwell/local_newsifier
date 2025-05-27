# Claude Bootstrap Instructions

> **IMPORTANT**: This is the PRIMARY guide Claude should read first when working on this project. This file contains critical instructions that override default behaviors.

## Quick Start for Claude

1. **Always read this file first** when starting work on this project
2. **Check AGENTS.md** to find other CLAUDE.md files for specific modules
3. **Follow the patterns** documented here consistently across all changes
4. **Use the tools** specified (rg instead of grep, fd instead of find, etc.)
5. **Run tests** before completing any task

## Core Principles

### 1. Always Use Modern CLI Tools
- `rg` (ripgrep) instead of `grep` - respects .gitignore, faster
- `fd` instead of `find` - simpler syntax, respects .gitignore
- `bat` instead of `cat` - syntax highlighting, line numbers
- `eza` instead of `ls` - better formatting, git integration
- `jq` for JSON processing
- `httpie`/`http` instead of `curl` - more intuitive

### 2. Git Workflow
- Create new branch immediately for any changes
- Commit early and often with descriptive messages
- Push after first commit and create PR using `gh pr create`
- Include issue number in PR title: "Fix X (Issue #123)"
- Monitor PR build (takes ~4 minutes) - use sleep loops to check
- Last line of responses should include PR and issue numbers

### 3. Testing Requirements
- Run full test suite before marking complete: `make test`
- Check GitHub Actions status after pushing
- For faster local testing: `poetry run pytest -n auto -q`
- Serial testing for debugging: `make test-serial`

### 4. Code Patterns to Follow
- Use SQLModel for all database models
- Use fastapi-injectable for dependency injection
- Return IDs not objects across session boundaries
- Mock external dependencies in tests
- Add newline at end of every file

### 5. Communication Style
- Be concise - max 4 lines unless asked for detail
- Skip unnecessary preambles/postambles
- One-word answers when appropriate
- Include file:line references for code locations

### 6. Consistency Rules
- **Error Handling**: Always use custom error classes from `src/local_newsifier/errors/`
- **Imports**: Group imports - stdlib, third-party, local (separated by blank lines)
- **Type Hints**: Always include type hints for function arguments and returns
- **Docstrings**: Use Google-style docstrings for all public functions/classes
- **File Operations**: Always use context managers (with statements)
- **Database Queries**: Never use raw SQL - always use SQLModel query builders
- **Tests**: Name test files with `test_` prefix, test functions with `test_` prefix
- **Fixtures**: Define fixtures in conftest.py files at appropriate levels

### 7. Common Mistakes to Avoid
- Don't use print() - use proper logging
- Don't hardcode credentials - use environment variables
- Don't catch generic Exception - catch specific exceptions
- Don't modify mutable default arguments
- Don't forget to close resources (use context managers)
- Don't use async patterns - the project is moving to sync-only
- Don't forget to add files to git before committing

# Local Newsifier Development Guide

## Project Overview
- News article analysis system using SQLModel, PostgreSQL, and dependency injection
- Focuses on entity tracking, sentiment analysis, and headline trend detection
- Uses NLP for entity recognition and relationship mapping
- Supports multiple content acquisition methods (RSS feeds, Apify web scraping)
- Moving from Celery to FastAPI Background Tasks for simpler task processing
- Deployed on Railway with web, worker, and scheduler processes

## Environment Setup

### Python Version
This project requires Python 3.10-3.12, with Python 3.12 recommended to match CI.

### Setup
```bash
# Complete installation (Poetry, dependencies, spaCy models, database)
make install

# For offline installation (requires pre-built wheels)
make install-offline

# For development setup with extra dependencies
make install-dev
```

See `docs/python_setup.md` for more details.

## Common Commands

### CLI Commands
- `nf help`: Show available commands and options
- `nf feeds list`: List configured RSS feeds
- `nf feeds add <URL>`: Add a new RSS feed
- `nf feeds show <ID>`: Show details for a specific feed
- `nf feeds remove <ID>`: Remove a feed
- `nf feeds update <ID>`: Update feed properties
- `nf feeds process <ID>`: Process a specific feed
- `nf db stats`: Show database statistics
- `nf db duplicates`: Find duplicate articles
- `nf db articles`: List articles with filtering options
- `nf db inspect <TABLE> <ID>`: Inspect a specific database record
- `nf apify test`: Test Apify API connection
- `nf apify scrape-content <URL>`: Scrape content using Apify
- `nf apify web-scraper <URL>`: Scrape websites using Apify's web-scraper
- `nf apify run-actor <ACTOR_ID>`: Run an Apify actor

### Webhook Testing Functions (Fish Shell)
- `test_webhook`: Main webhook testing function with customizable parameters
- `test_webhook_success`: Test successful actor run webhook
- `test_webhook_failure`: Test failed actor run webhook
- `test_webhook_batch`: Run multiple webhook test scenarios

### Standalone Scripts
- `python scripts/run_pipeline.py --url <URL>`: Process a single article
- `python scripts/demo_headline_trends.py --days 30 --interval day`: Analyze recent headlines
- `python scripts/demo_entity_tracking.py`: View entity tracking dashboard
- `python scripts/demo_sentiment_analysis.py`: Run sentiment analysis demo

### Development Commands
```bash
# Testing
make test              # Run tests in parallel
make test-serial       # Run tests serially (for debugging)
make test-coverage     # Run tests with coverage report

# Code quality
make lint              # Run linting (flake8 + mypy)
make format            # Auto-format code (isort + black)

# Running services
make run-api           # Run FastAPI server
make run-worker        # Run Celery worker
make run-beat          # Run Celery beat scheduler
make run-all           # Run all services (API, worker, beat)

# Database management
make db-init           # Initialize cursor-specific database
make db-reset          # Reset database (WARNING: deletes data)
make db-stats          # Show database statistics

# Cleanup
make clean             # Remove build artifacts

# Offline support
make build-wheels      # Build wheels for current platform
make build-wheels-linux # Build Linux wheels using Docker
```

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

> **Note:** Local Newsifier now uses the `fastapi-injectable` framework for dependency injection. The old custom container has been removed. See the [Dependency Injection Guide](docs/dependency_injection.md) for provider usage and the [DI Architecture Guide](docs/di_architecture.md) for design details.

#### FastAPI-Injectable System
- Newer components use the fastapi-injectable framework
- Provider functions are defined in `src/local_newsifier/di/providers.py`
- All providers use `use_cache=False` to create fresh instances on each request
- Example provider function:
```python
@injectable(use_cache=False)
def get_article_service(
    article_crud: Annotated[Any, Depends(get_article_crud)],
    session: Annotated[Session, Depends(get_session)]
):
    from local_newsifier.services.article_service import ArticleService

    return ArticleService(
        article_crud=article_crud,
        session_factory=lambda: session
    )
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

        results = self.trend_analyzer.extract_keywords([a.title for a in articles])

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
Use the `get_session` provider to obtain a database session:
```python
from typing import Annotated
from fastapi import Depends
from sqlmodel import Session

from local_newsifier.di.providers import get_session

def some_endpoint(
    session: Annotated[Session, Depends(get_session)]
):
    # Database operations here
```

For service methods:
```python
with self.session_factory() as session:
    # Use session for database operations
```

- Avoid carrying SQLModel objects between sessions to prevent "Instance is not bound to a Session" errors

### Best Practices
- Return IDs rather than SQLModel objects across session boundaries
- Use provider functions to lazily load dependencies and avoid circular imports
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
  - APIFY_WEBHOOK_SECRET (optional, for webhook validation)

### Webhook Configuration
- The `/webhooks/apify` endpoint accepts Apify webhook notifications
- Fish shell functions are available for easy webhook testing
- See `docs/apify_webhook_testing.md` for comprehensive testing guide

## Known Issues & Gotchas
- Environment variables must be properly managed in tests
- Database connections should be properly closed to avoid connection pool issues
- Type hints may need `TYPE_CHECKING` imports to avoid circular references
- SQLModel combines SQLAlchemy and Pydantic - use model_dump() not dict()
- SQLModel.exec() only takes one parameter - bind params to the query before calling
- Avoid passing SQLModel objects between sessions - use IDs instead
- Use runtime imports to break circular dependencies
- Redis is required for Celery - PostgreSQL is no longer supported as a broker


### Sync-Only Implementation

> **IMPORTANT**: The project is moving to sync-only implementations. Do not use async patterns in any new code. All code should use synchronous patterns:
> - Use `def` instead of `async def`
> - Use `Session` instead of `AsyncSession`
> - Use `session.exec()` instead of `await session.execute()`
> - Use `requests` instead of `httpx.AsyncClient`
> - Remove all `await` keywords
## Maintaining AGENTS.md

Whenever you add or remove a `CLAUDE.md` file anywhere in the repository, update the root `AGENTS.md` so Codex can find all of the guides.
