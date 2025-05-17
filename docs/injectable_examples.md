# Injectable Pattern Examples

This document provides practical code examples for implementing the injectable pattern in different parts of the Local Newsifier codebase. These examples are intended to serve as a quick reference for developers working on migrating components or creating new ones with fastapi-injectable.

## Table of Contents

- [Provider Functions](#provider-functions)
- [Services Examples](#services-examples)
- [Flow Examples](#flow-examples)
- [Tools Examples](#tools-examples)
- [CLI Commands Examples](#cli-commands-examples)
- [Testing Examples](#testing-examples)
- [Circular Dependency Examples](#circular-dependency-examples)

## Provider Functions

Provider functions are the foundation of the dependency injection system. They define how dependencies are created and injected.

### Database Session Provider

```python
@injectable(use_cache=False)
def get_session() -> Generator[Session, None, None]:
    """Provide a database session.
    
    The session is created fresh for each injection and 
    automatically closed when the context is exited.
    
    Yields:
        A database session
    """
    from local_newsifier.database.engine import get_session as get_db_session
    
    session = next(get_db_session())
    try:
        yield session
    finally:
        session.close()
```

### CRUD Provider

```python
@injectable(use_cache=False)
def get_entity_crud() -> EntityCRUD:
    """Provide the entity CRUD component.
    
    Returns:
        EntityCRUD instance
    """
    from local_newsifier.crud.entity import entity
    return entity
```

### Service Provider

```python
@injectable(use_cache=False)
def get_entity_service(
    entity_crud: Annotated[EntityCRUD, Depends(get_entity_crud)],
    canonical_entity_crud: Annotated[CanonicalEntityCRUD, Depends(get_canonical_entity_crud)],
    session: Annotated[Session, Depends(get_session)],
) -> EntityService:
    """Provide the EntityService with injected dependencies.
    
    Args:
        entity_crud: CRUD for entities
        canonical_entity_crud: CRUD for canonical entities
        session: Database session
        
    Returns:
        EntityService instance
    """
    from local_newsifier.services.entity_service import EntityService
    
    return EntityService(
        entity_crud=entity_crud,
        canonical_entity_crud=canonical_entity_crud,
        session=session
    )
```

### Tool Provider

```python
@injectable(use_cache=False)
def get_entity_extractor_tool(
    nlp_model: Annotated[spacy.language.Language, Depends(get_nlp_model)],
) -> EntityExtractor:
    """Provide the EntityExtractor with injected dependencies.
    
    Args:
        nlp_model: spaCy NLP model
        
    Returns:
        EntityExtractor instance
    """
    from local_newsifier.tools.extraction.entity_extractor import EntityExtractor
    
    return EntityExtractor(nlp_model=nlp_model)
```

## Services Examples

### Stateful Service Pattern

```python
@injectable(use_cache=False)
class ArticleService:
    """Service for managing articles."""
    
    def __init__(
        self,
        article_crud: Annotated[ArticleCRUD, Depends(get_article_crud)],
        session: Annotated[Session, Depends(get_session)],
    ):
        """Initialize with injected dependencies.
        
        Args:
            article_crud: CRUD operations for articles
            session: Database session
        """
        self.article_crud = article_crud
        self.session = session
    
    def get_article(self, article_id: int) -> Optional[Article]:
        """Get an article by ID."""
        return self.article_crud.get(self.session, id=article_id)
    
    def get_articles_by_source(self, source: str) -> List[Article]:
        """Get articles by source."""
        return self.article_crud.get_multi_by_source(self.session, source=source)
```

### Service with Integration

```python
@injectable(use_cache=False)
class ApifyService:
    """Service for interacting with Apify API."""
    
    def __init__(
        self,
        settings: Annotated[Settings, Depends(get_settings)],
        session: Annotated[Session, Depends(get_session)],
        apify_source_config_crud: Annotated[ApifySourceConfigCRUD, Depends(get_apify_source_config_crud)],
    ):
        """Initialize with injected dependencies.
        
        Args:
            settings: Application settings
            session: Database session
            apify_source_config_crud: CRUD for Apify source configs
        """
        self.settings = settings
        self.session = session
        self.apify_source_config_crud = apify_source_config_crud
        self._client = None
    
    @property
    def client(self):
        """Lazy-loaded Apify client."""
        if self._client is None:
            from apify_client import ApifyClient
            self._client = ApifyClient(self.settings.APIFY_TOKEN)
        return self._client
    
    def run_actor(self, actor_id: str, run_input: dict) -> dict:
        """Run an Apify actor."""
        return self.client.actor(actor_id).call(run_input=run_input)
```

## Flow Examples

### Flow Base Class (with Implementation)

```python
class EntityTrackingFlowBase:
    """Base implementation of entity tracking flow."""
    
    def __init__(
        self,
        entity_service,
        entity_tracker,
        entity_resolver,
    ):
        """Initialize with dependencies."""
        self.entity_service = entity_service
        self.entity_tracker = entity_tracker
        self.entity_resolver = entity_resolver
    
    def track_entities_in_article(self, article_id: int) -> dict:
        """Track entities in an article."""
        # Implementation using dependencies
        # ... actual implementation here
        return {"entities_tracked": 5}
```

### Injectable Flow Implementation

```python
@injectable(use_cache=False)
class EntityTrackingFlow(EntityTrackingFlowBase):
    """Injectable implementation of entity tracking flow."""
    
    def __init__(
        self,
        entity_service: Annotated[EntityService, Depends(get_entity_service)],
        entity_tracker: Annotated[EntityTracker, Depends(get_entity_tracker_tool)],
        entity_resolver: Annotated[EntityResolver, Depends(get_entity_resolver_tool)],
    ):
        """Initialize with injected dependencies."""
        super().__init__(
            entity_service=entity_service,
            entity_tracker=entity_tracker,
            entity_resolver=entity_resolver,
        )
```

### Flow with Multiple Dependencies

```python
@injectable(use_cache=False)
class NewsPipelineFlow(NewsPipelineFlowBase):
    """Injectable implementation of news pipeline flow."""
    
    def __init__(
        self,
        article_service: Annotated[ArticleService, Depends(get_article_service)],
        entity_service: Annotated[EntityService, Depends(get_entity_service)],
        entity_tracking_flow: Annotated[EntityTrackingFlow, Depends(get_entity_tracking_flow)],
        trend_analysis_flow: Annotated[TrendAnalysisFlow, Depends(get_trend_analysis_flow)],
        sentiment_analyzer: Annotated[SentimentAnalyzer, Depends(get_sentiment_analyzer_tool)],
    ):
        """Initialize with injected dependencies."""
        super().__init__(
            article_service=article_service,
            entity_service=entity_service,
            entity_tracking_flow=entity_tracking_flow,
            trend_analysis_flow=trend_analysis_flow,
            sentiment_analyzer=sentiment_analyzer,
        )
```

## Tools Examples

### Simple Tool Example

```python
@injectable(use_cache=False)
class EntityExtractor:
    """Tool for extracting entities from text."""
    
    def __init__(
        self,
        nlp_model: Annotated[spacy.language.Language, Depends(get_nlp_model)],
    ):
        """Initialize with injected dependencies."""
        self.nlp_model = nlp_model
    
    def extract_entities(self, text: str) -> List[Dict]:
        """Extract entities from text."""
        doc = self.nlp_model(text)
        entities = []
        
        for ent in doc.ents:
            entities.append({
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char
            })
        
        return entities
```

### Tool with Multiple Dependencies

```python
@injectable(use_cache=False)
class TrendAnalyzer:
    """Tool for analyzing trends in text data."""
    
    def __init__(
        self,
        nlp_model: Annotated[spacy.language.Language, Depends(get_nlp_model)],
        file_writer: Annotated[FileWriter, Depends(get_file_writer_tool)],
        settings: Annotated[Settings, Depends(get_settings)],
    ):
        """Initialize with injected dependencies."""
        self.nlp_model = nlp_model
        self.file_writer = file_writer
        self.settings = settings
    
    def extract_keywords(self, texts: List[str]) -> Dict[str, int]:
        """Extract and count keywords from texts."""
        # Implementation
        keywords = {}
        # ... actual implementation here
        return keywords
    
    def generate_report(self, keywords: Dict[str, int], output_path: Optional[str] = None) -> str:
        """Generate a report of keyword trends."""
        # Use file writer to output report
        path = output_path or f"{self.settings.OUTPUT_DIR}/trend_report.md"
        content = self._format_report(keywords)
        self.file_writer.write_file(path, content)
        return path
```

## CLI Commands Examples

### Simple CLI Command

```python
@click.command("stats")
@click.option("--detailed", is_flag=True, help="Show detailed statistics")
def db_stats_command(detailed: bool = False):
    """Show database statistics."""
    from local_newsifier.di.providers import get_session, get_article_crud, get_entity_crud
    from local_newsifier.container import container
    
    # Get dependencies through injectable providers
    session = get_injected_obj(get_session)
    article_crud = get_injected_obj(get_article_crud)
    entity_crud = get_injected_obj(get_entity_crud)
    
    # Get statistics
    article_count = article_crud.count(session)
    entity_count = entity_crud.count(session)
    
    # Display results
    click.echo(f"Database Statistics:")
    click.echo(f"Articles: {article_count}")
    click.echo(f"Entities: {entity_count}")
    
    if detailed:
        # Show more detailed stats
        # ... additional code here
        pass
```

### CLI Command with Complex Logic

```python
def process_feed_command(
    feed_id: int,
    limit: Optional[int] = None,
    rss_feed_service: Optional[RSSFeedService] = None,
):
    """Process a feed with injectable dependencies."""
    # Get dependencies if not provided
    if rss_feed_service is None:
        rss_feed_service = get_injected_obj(get_rss_feed_service)
    
    try:
        # Process the feed
        result = rss_feed_service.process_feed(feed_id, limit=limit)
        
        # Display results
        typer.echo(f"Processed {result['processed']} articles from feed {feed_id}")
        typer.echo(f"New articles: {result['new']}")
        typer.echo(f"Updated articles: {result['updated']}")
        
        return result
    except Exception as e:
        typer.echo(f"Error processing feed {feed_id}: {str(e)}", err=True)
        raise

# CLI command registration
@click.command("process")
@click.argument("feed_id", type=int)
@click.option("--limit", type=int, help="Limit the number of articles to process")
def process_feed_cli(feed_id: int, limit: Optional[int] = None):
    """Process articles from an RSS feed."""
    return process_feed_command(feed_id, limit)
```

## Testing Examples

### Testing a Service

```python
def test_article_service_get_article():
    """Test ArticleService.get_article method."""
    # Create mock dependencies
    mock_article_crud = Mock()
    mock_session = Mock()
    
    # Configure mocks
    test_article = Article(id=1, title="Test Article", content="Content")
    mock_article_crud.get.return_value = test_article
    
    # Create service with mock dependencies
    service = ArticleService(
        article_crud=mock_article_crud,
        session=mock_session
    )
    
    # Execute method
    article = service.get_article(1)
    
    # Verify behavior
    mock_article_crud.get.assert_called_once_with(mock_session, id=1)
    assert article == test_article
```

### Testing with Monkeypatch

```python
@pytest.fixture
def patch_injectable_dependencies(monkeypatch):
    """Patch injectable dependencies for tests."""
    # Create mocks
    mock_entity_crud = Mock()
    mock_session = Mock()
    
    # Configure mocks
    test_entity = Entity(id=1, name="Test Entity", type="PERSON")
    mock_entity_crud.get.return_value = test_entity
    
    # Patch provider functions
    monkeypatch.setattr("local_newsifier.di.providers.get_entity_crud", lambda: mock_entity_crud)
    monkeypatch.setattr("local_newsifier.di.providers.get_session", lambda: mock_session)
    
    return {
        "entity_crud": mock_entity_crud,
        "session": mock_session,
        "test_entity": test_entity
    }

def test_entity_service_with_patched_dependencies(patch_injectable_dependencies):
    """Test EntityService using patched dependencies."""
    # Import service (after dependencies are patched)
    from local_newsifier.services.entity_service import EntityService
    
    # Get patched mocks
    mocks = patch_injectable_dependencies
    
    # Create service (it will get patched dependencies)
    service = EntityService(
        entity_crud=mocks["entity_crud"],
        session=mocks["session"],
        canonical_entity_crud=Mock()
    )
    
    # Execute method
    entity = service.get_entity(1)
    
    # Verify behavior
    mocks["entity_crud"].get.assert_called_once_with(mocks["session"], id=1)
    assert entity == mocks["test_entity"]
```

### Testing Async Components

```python
@pytest.mark.asyncio
async def test_async_service(event_loop_fixture):
    """Test an async service with proper event loop management."""
    # Create mock dependencies
    mock_client = AsyncMock()
    mock_settings = Mock(APIFY_TOKEN="test_token")
    
    # Configure mock behavior
    mock_client.actor().call.return_value = {"result": "data"}
    
    # Create service with mocks
    service = AsyncApifyService(
        settings=mock_settings,
        client=mock_client
    )
    
    # Execute async method
    result = await service.run_actor("test_actor", {"input": "data"})
    
    # Verify behavior
    mock_client.actor.assert_called_once_with("test_actor")
    mock_client.actor().call.assert_called_once_with(run_input={"input": "data"})
    assert result == {"result": "data"}
```

## Circular Dependency Examples

### Factory Provider with Lazy Loading

```python
@injectable(use_cache=False)
def get_service_a():
    """Provider for ServiceA that breaks circular dependency."""
    # Import related components inside function for lazy loading
    from local_newsifier.services.service_b import ServiceB
    from local_newsifier.di.providers import get_service_b
    
    # Create ServiceB lazily to break the circular dependency
    service_b = get_service_b()
    
    # Now import and create ServiceA
    from local_newsifier.services.service_a import ServiceA
    return ServiceA(service_b=service_b)
```

### Method Injection

```python
@injectable(use_cache=False)
class ServiceA:
    """Service that avoids circular dependency at initialization."""
    
    def __init__(
        self,
        # No circular dependencies here
        other_dependency: Annotated[OtherDependency, Depends(get_other_dependency)],
    ):
        """Initialize without circular dependencies."""
        self.other_dependency = other_dependency
    
    def method_needing_service_b(
        self,
        service_b: Annotated[ServiceB, Depends(get_service_b)]
    ):
        """Method that uses ServiceB, injected at method level."""
        return service_b.do_something()
```

### Interface Abstraction

```python
# Define interface
class EntityResolverInterface(Protocol):
    """Interface for entity resolution."""
    
    def resolve_entity(self, entity_name: str) -> str:
        """Resolve an entity name to canonical form."""
        ...

# Service using the interface
@injectable(use_cache=False)
class EntityService:
    """Service that depends on interface instead of concrete implementation."""
    
    def __init__(
        self,
        entity_resolver: Annotated[EntityResolverInterface, Depends(get_entity_resolver)],
        session: Annotated[Session, Depends(get_session)],
    ):
        """Initialize with interface dependency."""
        self.entity_resolver = entity_resolver
        self.session = session
    
    def process_entity(self, entity_name: str):
        """Process an entity using the resolver."""
        canonical_name = self.entity_resolver.resolve_entity(entity_name)
        # Process with canonical name
        return canonical_name
```