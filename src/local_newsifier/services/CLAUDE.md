# Local Newsifier Services Guide

## Overview
The services module contains business logic that coordinates between CRUD operations (database access) and tools (processing logic). Services manage transactions, implement business rules, and provide a clean API for higher-level components.

> **IMPORTANT**: fastapi-injectable is now the sole dependency injection system. All services should follow the injectable pattern described in the "Injectable Service Pattern" section below.

## Key Service Types

### Content Services
- **ArticleService**: Manages article creation, fetching, and processing
- **RSSFeedService**: Manages RSS feed configuration and article extraction
- **ApifyService**: Manages Apify web scraping integration
- Located in `services/article_service.py`, `services/rss_feed_service.py`, `services/apify_service.py`

### Analysis Services
- **AnalysisService**: Provides analysis operations for articles and entities
- **EntityService**: Manages entity tracking and relationship analysis
- Located in `services/analysis_service.py`, `services/entity_service.py`

### Pipeline Services
- **NewsPipelineService**: Coordinates the end-to-end news processing pipeline
- Located in `services/news_pipeline_service.py`

## Service Patterns

### Service Initialization
Services accept dependencies through constructor injection:

```python
class EntityService:
    def __init__(
        self,
        entity_crud: Annotated[EntityCRUD, Depends(get_entity_crud)],
        canonical_entity_crud: Annotated[CanonicalEntityCRUD, Depends(get_canonical_entity_crud)],
        entity_relationship_crud: Annotated[EntityRelationshipCRUD, Depends(get_entity_relationship_crud)],
        sentiment_analyzer: Annotated[SentimentAnalyzer, Depends(get_sentiment_analyzer_tool)],
        entity_extractor: Annotated[EntityExtractor, Depends(get_entity_extractor_tool)],
        session: Annotated[Session, Depends(get_session)],
    ):
        """Initialize the entity service with injected dependencies."""
        self.entity_crud = entity_crud
        self.canonical_entity_crud = canonical_entity_crud
        self.entity_relationship_crud = entity_relationship_crud
        self.sentiment_analyzer = sentiment_analyzer
        self.entity_extractor = entity_extractor
        self.session = session
```


### Transaction Management
Services manage database transactions using context managers:

```python
def create_entity(self, entity_data):
    """Create a new entity.

    Args:
        entity_data: Dictionary with entity data

    Returns:
        Created entity ID
    """
    session = self.session
    # Create entity in database
    entity = self.entity_crud.create(
        session,
        Entity(**entity_data)
    )

        # Return ID, not entity object
        return entity.id
```

### Return Values
Services return IDs or data dicts, not SQLModel objects:

```python
def get_entity(self, entity_id):
    """Get entity by ID.

    Args:
        entity_id: ID of the entity to get

    Returns:
        Entity data as dictionary, or None if not found
    """
    entity = self.entity_crud.get(self.session, entity_id)
    if not entity:
        return None

    # Return data dict, not entity object
    return entity.model_dump()
```

### Tool Integration
Services coordinate between database and tools:

```python
def analyze_entity_sentiment(self, entity_id):
    """Analyze sentiment for an entity.

    Args:
        entity_id: ID of the entity to analyze

    Returns:
        Sentiment analysis result
    """
    # Get entity from database
    entity = self.entity_crud.get(self.session, entity_id)
    if not entity:
        raise ValueError(f"Entity not found: {entity_id}")

    # Get context for entity
    context = entity.sentence_context or ""

    # Analyze sentiment using injected analyzer
    sentiment = self.sentiment_analyzer.analyze_sentiment(context)

    # Create analysis result
    analysis_result = AnalysisResult(
        entity_id=entity_id,
        analysis_type="sentiment",
        result_data=sentiment,
        created_at=datetime.now(timezone.utc)
    )

    # Save to database
    result = self.analysis_result_crud.create(self.session, analysis_result)

    # Return result ID and data
    return result.id, analysis_result.result_data

        # Return result ID and data
        return {
            "id": result.id,
            "entity_id": entity_id,
            "sentiment": sentiment
        }
```

### State-Based Services
Services may use state objects for complex operations:

```python
def process_article_with_state(self, state: EntityTrackingState) -> EntityTrackingState:
    """Process an article with tracking state.

    Args:
        state: Current processing state

    Returns:
        Updated state with processing results
    """
    try:
        # Get article from database
        article = self.article_crud.get(self.session, state.article_id)
        if not article:
            raise ValueError(f"Article not found: {state.article_id}")

            # Extract entities using injected tool
            entities = self.entity_extractor.extract_entities(article.content)

            # Update state with extracted entities
            state.entities = entities
            state.add_log(f"Extracted {len(entities)} entities")

            # Save entities to database
            for entity_data in entities:
                entity = Entity(
                    article_id=article.id,
                    text=entity_data["text"],
                    entity_type=entity_data["entity_type"],
                    confidence=entity_data.get("confidence", 1.0)
                )
                self.entity_crud.create(session, entity)

            # Update state to success
            state.status = TrackingStatus.SUCCESS

    except Exception as e:
        # Update state with error
        state.status = TrackingStatus.ERROR
        state.set_error("entity_service.process_article", e)

    return state
```

### External API Integration
Services encapsulate interactions with external APIs:

```python
class ApifyService:
    def __init__(self, token=None):
        """Initialize the Apify service.

        Args:
            token: API token for Apify authentication
        """
        self._token = token
        self._client = None

    @property
    def client(self):
        """Get the Apify client."""
        if self._client is None:
            from apify_client import ApifyClient
            token = self._token or settings.APIFY_TOKEN
            self._client = ApifyClient(token)
        return self._client

    def run_actor(self, actor_id, run_input):
        """Run an Apify actor.

        Args:
            actor_id: ID of the actor to run
            run_input: Input data for the actor

        Returns:
            Result of the actor run
        """
        return self.client.actor(actor_id).call(run_input=run_input)
```

## Service Providers

Services are exposed through provider functions:

```python
from typing import Annotated
from fastapi import Depends
from fastapi_injectable import injectable

@injectable(use_cache=False)
def get_entity_service(
    entity_crud: Annotated[EntityCRUD, Depends(get_entity_crud)],
    canonical_entity_crud: Annotated[CanonicalEntityCRUD, Depends(get_canonical_entity_crud)],
    entity_relationship_crud: Annotated[EntityRelationshipCRUD, Depends(get_entity_relationship_crud)],
    session: Annotated[Session, Depends(get_session)],
) -> EntityService:
    return EntityService(
        entity_crud=entity_crud,
        canonical_entity_crud=canonical_entity_crud,
        entity_relationship_crud=entity_relationship_crud,
        session=session,
    )
```

## Best Practices

### Service Design
- Keep services focused on specific business domains
- Use meaningful method names that reflect business operations
- Implement proper error handling and validation
- Encapsulate complex logic behind simple interfaces
- Return IDs or data dicts, not ORM objects

### Session Management
- Use context managers for database sessions
- Don't pass SQLModel objects between sessions
- Commit transactions explicitly at the end of operations
- Handle errors and rollback transactions when needed

### Dependency Injection
- Accept dependencies through constructor parameters
- Ensure provider functions supply all required dependencies
- Verify required dependencies are available
- Use lazy loading for expensive dependencies

### Error Handling
- Provide clear error messages
- Log errors with appropriate context
- Translate technical errors to business-level errors
- Implement retry logic for transient failures

### Testing
- Mock dependencies for unit testing
- Test happy paths and error cases
- Verify database interactions
- Test integration with tools and external APIs

## Injectable Service Pattern

Services are transitioning to use fastapi-injectable for dependency injection. This section describes the new pattern.

### Injectable Service Definition

```python
from typing import Annotated
from fastapi import Depends
from fastapi_injectable import injectable

@injectable
class InjectableEntityService:
    """Entity service using fastapi-injectable."""

    def __init__(
        self,
        entity_crud: Annotated[EntityCRUD, Depends(get_entity_crud)],
        canonical_entity_crud: Annotated[CanonicalEntityCRUD, Depends(get_canonical_entity_crud)],
        session: Annotated[Session, Depends(get_session)],
    ):
        self.entity_crud = entity_crud
        self.canonical_entity_crud = canonical_entity_crud
        self.session = session
```

### Session Usage in Injectable Services

In injectable services, the session is typically injected directly:

```python
def process_entity(self, entity_id: int):
    """Process an entity.

    Args:
        entity_id: ID of the entity to process

    Returns:
        Processed entity data
    """
    # Use the injected session directly
    entity = self.entity_crud.get(self.session, entity_id)
    if not entity:
        raise ValueError(f"Entity not found: {entity_id}")

    # Process entity...

    # Return processed data
    return entity.model_dump()
```

### Testing Injectable Services

Injectable services can be tested by providing mock dependencies directly:

```python
def test_injectable_service(patch_injectable_dependencies):
    # Get mocks from fixture
    mocks = patch_injectable_dependencies

    # Create service with mock dependencies
    service = InjectableEntityService(
        entity_crud=mocks["entity_crud"],
        canonical_entity_crud=mocks["canonical_entity_crud"],
        session=mocks["session"]
    )

    # Test the service
    result = service.process_entity(1)
    assert result is not None

    # Verify mock calls
    mocks["entity_crud"].get.assert_called_once_with(mocks["session"], 1)
```

For more information on the migration to fastapi-injectable, see `docs/fastapi_injectable.md`.

## Async Services

The project now includes async versions of key services for handling async operations, particularly useful for web endpoints and concurrent processing.

### Available Async Services
- **ApifyServiceAsync**: Async version of the Apify integration service
- **ApifyWebhookServiceAsync**: Handles webhook notifications asynchronously
- Located in `services/apify_service_async.py`, `services/apify_webhook_service_async.py`

### Async Service Pattern

Async services follow similar patterns but use async/await syntax:

```python
class ApifyWebhookServiceAsync:
    """Async service for handling Apify webhooks."""

    def __init__(self, session: AsyncSession, webhook_secret: Optional[str] = None):
        """Initialize webhook service.

        Args:
            session: Async database session
            webhook_secret: Optional webhook secret for signature validation
        """
        self.session = session
        self.webhook_secret = webhook_secret
        self.apify_service = ApifyServiceAsync()

    async def process_webhook(self, data: Dict) -> Dict:
        """Process webhook notification asynchronously.

        Args:
            data: Webhook payload data

        Returns:
            Processing result
        """
        # Save raw webhook data
        webhook_raw = ApifyWebhookRaw(
            event_type=data.get("eventType"),
            run_id=data.get("runId"),
            actor_id=data.get("actorId"),
            data=data
        )
        self.session.add(webhook_raw)
        await self.session.flush()  # Ensure ID is generated

        # Process based on event type
        if data.get("eventType") == "ACTOR.RUN.SUCCEEDED":
            await self._process_successful_run(data)

        return {"status": "processed", "webhook_id": webhook_raw.id}
```

### Async Query Patterns

Async services use SQLAlchemy's async query syntax:

```python
async def get_articles_by_source(self, source_id: str) -> List[Dict]:
    """Get articles by source ID asynchronously."""
    # Use select() with await
    stmt = select(Article).where(Article.source_id == source_id)
    result = await self.session.execute(stmt)
    articles = result.scalars().all()

    # Return data dicts
    return [article.model_dump() for article in articles]
```

### When to Use Async Services

**Use Async Services When:**
- Handling webhook endpoints in FastAPI
- Processing multiple I/O operations concurrently
- Integrating with async external APIs
- Working within async request contexts

**Use Sync Services When:**
- Running CLI commands
- Processing background tasks with Celery
- Working with legacy code that doesn't support async
- Simple sequential operations

### Async Transaction Management

Async services handle transactions differently:

```python
async def create_article_async(self, article_data: Dict) -> int:
    """Create article with async transaction."""
    try:
        article = Article(**article_data)
        self.session.add(article)
        await self.session.flush()  # Flush to get ID
        await self.session.commit()
        return article.id
    except Exception as e:
        await self.session.rollback()
        logger.error(f"Failed to create article: {e}")
        raise
```

### Testing Async Services

Test async services using pytest-asyncio:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_async_webhook_service():
    # Mock async session
    mock_session = MagicMock()
    mock_session.execute = AsyncMock()
    mock_session.flush = AsyncMock()
    mock_session.commit = AsyncMock()

    # Create service
    service = ApifyWebhookServiceAsync(session=mock_session)

    # Test async method
    result = await service.process_webhook({"eventType": "test"})
    assert result["status"] == "processed"

    # Verify async calls
    mock_session.flush.assert_called_once()
```

### Async Service Best Practices

1. **Always use await**: Don't forget to await async operations
2. **Handle exceptions**: Use try/except with proper rollback
3. **Avoid blocking operations**: Don't use sync I/O in async services
4. **Use async context managers**: For resource management
5. **Test thoroughly**: Async code can have subtle timing issues
