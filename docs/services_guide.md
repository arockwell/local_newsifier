# Services Guide

## Return Standards

Services **must** return:
* `<Model>Read` SQLModel DTOs for single entities
* `List[<Model>Read]` for collections  
* Primitive IDs when only identifiers are needed
* `None` for not-found cases (don't raise exceptions for missing data)

Services **must not** return:
* Session-bound SQLModel table instances
* Raw `dict` payloads
* Mutable objects that could affect database state

## Method Naming Conventions

- `get_<entity>()` - retrieve single entity, returns None if not found
- `list_<entities>()` - retrieve multiple entities with optional filtering
- `create_<entity>()` - create new entity, return created DTO
- `update_<entity>()` - update existing entity, return updated DTO
- `delete_<entity>()` - delete entity, return boolean success

## DTO Structure & Relationships

- Use `<Model>Read` DTOs that include only necessary fields for API responses
- For nested relationships, prefer IDs over full nested DTOs to avoid deep object graphs
- Include related entity IDs as separate fields when needed
- Use pagination for collections with `limit` and `offset` parameters

## Error Handling Standards

- Raise `ValidationError` for invalid input data
- Raise `NotFoundError` for required entities that don't exist  
- Log errors but don't expose internal details in exceptions
- Use structured error responses with consistent format
- Return `None` for optional lookups that don't find results

## Input Parameters

- Accept primitive types (IDs, strings, numbers) rather than SQLModel instances
- Use Pydantic models for complex input validation
- Provide sensible defaults for optional parameters
- Validate input at service boundaries, not just at API level

## Session Management

- Services should accept session factories, not sessions directly
- Use `with session_factory() as session:` pattern within service methods
- Keep transaction boundaries within individual service methods
- Don't pass SQLModel objects between sessions to avoid "Instance is not bound to a Session" errors
- Use runtime imports to avoid circular dependencies with session providers

## Async Patterns

- Services should be synchronous by default for simplicity
- Use async only when interfacing with async external APIs
- If async is needed, make the entire service async, not just individual methods
- Document async requirements clearly in service docstrings

## Logging & Monitoring

- Log at INFO level for successful operations with significant business impact
- Log at WARNING level for recoverable errors or unexpected but handled conditions
- Log at ERROR level for unrecoverable errors
- Include relevant entity IDs and operation context in log messages
- Use structured logging with consistent field names

## Testing Standards

- Mock external dependencies but use real database sessions in service tests
- Create test data using factories or fixtures, not manual SQL
- Test both success and error cases for each service method
- Verify return types match expected DTOs
- Test session management and cleanup

## Example Service Implementation

```python
from typing import List, Optional
from sqlmodel import Session
from local_newsifier.models.article import Article, ArticleRead
from local_newsifier.crud.article import ArticleCRUD

class ArticleService:
    def __init__(self, article_crud: ArticleCRUD, session_factory):
        self.article_crud = article_crud
        self.session_factory = session_factory

    def get_article(self, article_id: int) -> Optional[ArticleRead]:
        """Get article by ID, returns None if not found."""
        with self.session_factory() as session:
            article = self.article_crud.get(session, article_id)
            return ArticleRead.model_validate(article) if article else None

    def list_articles(self, limit: int = 50, offset: int = 0) -> List[ArticleRead]:
        """List articles with pagination."""
        with self.session_factory() as session:
            articles = self.article_crud.get_multi(session, skip=offset, limit=limit)
            return [ArticleRead.model_validate(article) for article in articles]

    def create_article(self, title: str, content: str, url: str) -> ArticleRead:
        """Create new article and return created DTO."""
        with self.session_factory() as session:
            article = self.article_crud.create(session, {
                "title": title,
                "content": content, 
                "url": url
            })
            session.commit()
            return ArticleRead.model_validate(article)
```

## Migration Strategy

When updating existing services to follow these standards:

1. **Create missing `<Model>Read` DTOs first** - All core models now have Read DTOs:
   - `ArticleRead`, `EntityRead`, `AnalysisResultRead`
   - `RSSFeedRead`, `RSSFeedProcessingLogRead`
   - `ApifySourceConfigRead`, `ApifyJobRead`, `ApifyDatasetItemRead`, `ApifyCredentialsRead`, `ApifyWebhookRead`
2. Update service return types one method at a time
3. Update corresponding tests to verify new return types
4. Update API endpoints to work with new service responses
5. Remove any raw dict handling from calling code

### Helper Function for Converting SQLModel to Read DTO

```python
def to_read_dto(instance: SQLModel, read_dto_class: type) -> SQLModel:
    """Convert a SQLModel instance to its Read DTO equivalent."""
    return read_dto_class.model_validate(instance)
```