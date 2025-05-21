# Injectable Patterns Guide

This guide provides comprehensive documentation and examples for using the injectable pattern in Local Newsifier.

The migration from the previous container-based system is complete. The migration guide below is kept for reference when updating any remaining legacy code.

## Table of Contents

1. [Overview](#overview)
2. [Component Patterns](#component-patterns)
   - [Services](#services)
   - [Flow Components](#flow-components)
   - [Tools](#tools)
   - [CLI Commands](#cli-commands)
3. [Migration Guide](#migration-guide)
   - [Step-by-Step Migration](#step-by-step-migration)
   - [Before/After Examples](#beforeafter-examples)
4. [Testing Guide](#testing-guide)
   - [Unit Testing Injectable Components](#unit-testing-injectable-components)
   - [Integration Testing](#integration-testing)
   - [Mocking Strategies](#mocking-strategies)
5. [Handling Circular Dependencies](#handling-circular-dependencies)
6. [Troubleshooting](#troubleshooting)
   - [Common Issues](#common-issues)
   - [Performance Considerations](#performance-considerations)
   - [Debugging Dependency Resolution](#debugging-dependency-resolution)

## Overview

The Local Newsifier project uses the `fastapi-injectable` framework for dependency injection. This guide provides practical examples and patterns to follow when implementing components.

### Key Principles

1. **Always use `use_cache=False`**
   
   For consistency and safety, we've standardized on `use_cache=False` for all components:

   ```python
   @injectable(use_cache=False)
   ```

2. **Explicit Dependencies**
   
   Always declare dependencies explicitly in constructors using `Annotated` and `Depends`:

   ```python
   def __init__(
       self,
       session: Annotated[Session, Depends(get_session)],
       entity_crud: Annotated[EntityCRUD, Depends(get_entity_crud)]
   ):
   ```

3. **Type Safety**
   
   Always use proper type annotations for better IDE support and error checking.

## Component Patterns

### Services

Services are stateful components that implement business logic and often interact with the database.

#### Example: Entity Service

```python
from typing import Annotated, List, Optional
from fastapi import Depends
from fastapi_injectable import injectable
from sqlmodel import Session

from local_newsifier.crud.entity import EntityCRUD, entity as entity_crud
from local_newsifier.crud.canonical_entity import CanonicalEntityCRUD, canonical_entity as canonical_entity_crud
from local_newsifier.models.entity import Entity, CanonicalEntity
from local_newsifier.di.providers import get_entity_crud, get_canonical_entity_crud, get_session

@injectable(use_cache=False)
class EntityService:
    """Service for managing entities with injectable dependencies."""
    
    def __init__(
        self,
        entity_crud: Annotated[EntityCRUD, Depends(get_entity_crud)],
        canonical_entity_crud: Annotated[CanonicalEntityCRUD, Depends(get_canonical_entity_crud)],
        session: Annotated[Session, Depends(get_session)],
    ):
        """Initialize with injected dependencies.
        
        Args:
            entity_crud: CRUD operations for entities
            canonical_entity_crud: CRUD operations for canonical entities
            session: Database session
        """
        self.entity_crud = entity_crud
        self.canonical_entity_crud = canonical_entity_crud
        self.session = session
    
    def get_entity(self, entity_id: int) -> Optional[Entity]:
        """Get an entity by ID.
        
        Args:
            entity_id: The entity ID
            
        Returns:
            The entity or None if not found
        """
        return self.entity_crud.get(self.session, id=entity_id)
    
    def get_canonical_entities(self) -> List[CanonicalEntity]:
        """Get all canonical entities.
        
        Returns:
            List of canonical entities
        """
        return self.canonical_entity_crud.get_all(self.session)
```

#### Provider Function for Services

```python
@injectable(use_cache=False)
def get_entity_service(
    entity_crud: Annotated[EntityCRUD, Depends(get_entity_crud)],
    canonical_entity_crud: Annotated[CanonicalEntityCRUD, Depends(get_canonical_entity_crud)],
    session: Annotated[Session, Depends(get_session)],
) -> EntityService:
    """Provide EntityService with injected dependencies."""
    from local_newsifier.services.entity_service import EntityService
    
    return EntityService(
        entity_crud=entity_crud,
        canonical_entity_crud=canonical_entity_crud,
        session=session
    )
```

### Flow Components

Flow components orchestrate higher-level workflows by combining services and tools. We use a base class pattern to separate core functionality from dependency concerns.

#### Example: Entity Tracking Flow

```python
# Base class (dependency-free implementation)
class EntityTrackingFlowBase:
    """Base implementation of entity tracking flow."""
    
    def __init__(
        self,
        entity_service,
        entity_tracker,
        entity_resolver,
    ):
        """Initialize with dependencies.
        
        Args:
            entity_service: Service for entity operations
            entity_tracker: Tool for tracking entity mentions
            entity_resolver: Tool for resolving entities
        """
        self.entity_service = entity_service
        self.entity_tracker = entity_tracker
        self.entity_resolver = entity_resolver
    
    def track_entities_in_article(self, article_id: int) -> dict:
        """Track entities in an article.
        
        Args:
            article_id: The article ID
            
        Returns:
            Dictionary with tracking results
        """
        # Implementation using dependencies
        # ...
        return {"tracked_entities": [...]}

# Injectable implementation
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

#### Provider Function for Flows

```python
@injectable(use_cache=False)
def get_entity_tracking_flow(
    entity_service: Annotated[EntityService, Depends(get_entity_service)],
    entity_tracker: Annotated[EntityTracker, Depends(get_entity_tracker_tool)],
    entity_resolver: Annotated[EntityResolver, Depends(get_entity_resolver_tool)],
) -> EntityTrackingFlow:
    """Provide EntityTrackingFlow with injected dependencies."""
    from local_newsifier.flows.entity_tracking_flow import EntityTrackingFlow
    
    return EntityTrackingFlow(
        entity_service=entity_service,
        entity_tracker=entity_tracker,
        entity_resolver=entity_resolver,
    )
```

### Tools

Tools provide utility functions for specific processing tasks. They can be stateless (pure functions) or stateful.

#### Example: Entity Extractor Tool

```python
from typing import Annotated, Dict, List, Optional
from fastapi import Depends
from fastapi_injectable import injectable
import spacy

from local_newsifier.di.providers import get_nlp_model

@injectable(use_cache=False)
class EntityExtractor:
    """Tool for extracting entities from text using NLP."""
    
    def __init__(
        self,
        nlp_model: Annotated[spacy.language.Language, Depends(get_nlp_model)],
    ):
        """Initialize with injected dependencies.
        
        Args:
            nlp_model: The spaCy NLP model
        """
        self.nlp_model = nlp_model
    
    def extract_entities(self, text: str) -> List[Dict]:
        """Extract entities from text.
        
        Args:
            text: The text to process
            
        Returns:
            List of extracted entities
        """
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

#### Provider Function for Tools

```python
@injectable(use_cache=False)
def get_entity_extractor_tool(
    nlp_model: Annotated[spacy.language.Language, Depends(get_nlp_model)],
) -> EntityExtractor:
    """Provide EntityExtractor with injected dependencies."""
    from local_newsifier.tools.extraction.entity_extractor import EntityExtractor
    
    return EntityExtractor(nlp_model=nlp_model)
```

### CLI Commands

CLI commands can use injectable dependencies to access services and tools.

#### Example: Feed Processing Command

```python
import click
import typer
from typing import Annotated, Optional
from fastapi import Depends
from fastapi_injectable import injectable, get_injected_obj

from local_newsifier.di.providers import get_rss_feed_service
from local_newsifier.services.rss_feed_service import RSSFeedService

# Command implementation
def process_feed_command(
    feed_id: int,
    limit: Optional[int] = None,
    rss_feed_service: RSSFeedService = None
):
    """Process articles from an RSS feed.
    
    Args:
        feed_id: The feed ID to process
        limit: Optional limit for the number of articles to process
        rss_feed_service: The RSS feed service (injected)
    """
    # Get dependencies if not provided
    if rss_feed_service is None:
        rss_feed_service = get_injected_obj(get_rss_feed_service)
    
    # Command implementation
    result = rss_feed_service.process_feed(feed_id, limit=limit)
    typer.echo(f"Processed {result['processed']} articles from feed {feed_id}")
    return result

# CLI command registration
@click.command("process")
@click.argument("feed_id", type=int)
@click.option("--limit", type=int, help="Limit the number of articles to process")
def process_feed_cli(feed_id: int, limit: Optional[int] = None):
    """Process articles from an RSS feed."""
    process_feed_command(feed_id, limit)
```

## Implementation Guide

### Step-by-Step Process

Follow these steps to create an injectable component:

1. **Identify Dependencies**
   - List all dependencies used by the component
   - Determine if they have provider functions already

2. **Create Missing Provider Functions**
   - If a dependency doesn't have a provider function, create one in `di/providers.py`
   - Follow the naming convention: `get_[component_name]`

3. **Create a Base Class (for flows)**
   - For complex flows, create a base class with the core implementation
   - Move the implementation logic to the base class

4. **Add Injectable Decorator**
   - Add the `@injectable(use_cache=False)` decorator to the class
   - Update constructor to use `Annotated[Type, Depends()]` for dependencies

5. **Update Tests**
   - Update tests to work with the injectable approach
   - Ensure existing functionality remains unchanged

### Before/After Examples

#### Service Migration Example

**Before (legacy pattern using `SessionManager`):**
```python
class ArticleService:
    def __init__(self, article_crud=None, session_factory=None):
        self.article_crud = article_crud or ArticleCRUD()
        self.session_factory = session_factory or SessionManager

    def get_article(self, article_id):
        with self.session_factory() as session:
            return self.article_crud.get(session, id=article_id)
```

**After:**
```python
from typing import Annotated, Optional
from fastapi import Depends
from fastapi_injectable import injectable
from sqlmodel import Session

from local_newsifier.di.providers import get_article_crud, get_session
from local_newsifier.crud.article import ArticleCRUD
from local_newsifier.models.article import Article

@injectable(use_cache=False)
class ArticleService:
    def __init__(
        self,
        article_crud: Annotated[ArticleCRUD, Depends(get_article_crud)],
        session: Annotated[Session, Depends(get_session)],
    ):
        self.article_crud = article_crud
        self.session = session
    
    def get_article(self, article_id: int) -> Optional[Article]:
        return self.article_crud.get(self.session, id=article_id)
```

#### Flow Migration Example

**Before:**
```python
class NewsPipelineFlow:
    def __init__(self, article_service=None, entity_service=None, entity_tracker=None):
        self.article_service = article_service or ArticleService()
        self.entity_service = entity_service or EntityService()
        self.entity_tracker = entity_tracker or EntityTracker()
    
    def process_article(self, article_id):
        article = self.article_service.get_article(article_id)
        entities = self.entity_tracker.extract_entities(article.content)
        return {"article": article, "entities": entities}
```

**After:**
```python
# Base class
class NewsPipelineFlowBase:
    def __init__(self, article_service, entity_service, entity_tracker):
        self.article_service = article_service
        self.entity_service = entity_service
        self.entity_tracker = entity_tracker
    
    def process_article(self, article_id):
        article = self.article_service.get_article(article_id)
        entities = self.entity_tracker.extract_entities(article.content)
        return {"article": article, "entities": entities}

# Injectable class
@injectable(use_cache=False)
class NewsPipelineFlow(NewsPipelineFlowBase):
    def __init__(
        self,
        article_service: Annotated[ArticleService, Depends(get_article_service)],
        entity_service: Annotated[EntityService, Depends(get_entity_service)],
        entity_tracker: Annotated[EntityTracker, Depends(get_entity_tracker_tool)],
    ):
        super().__init__(
            article_service=article_service,
            entity_service=entity_service,
            entity_tracker=entity_tracker,
        )
```

## Testing Guide

### Unit Testing Injectable Components

Unit testing injectable components involves:

1. **Mock Provider Functions** - Override provider functions to return mocks
2. **Direct Instantiation** - Instantiate with mocked dependencies
3. **Verify Interactions** - Verify interactions with dependencies

#### Example: Testing a Service

```python
import pytest
from unittest.mock import Mock, patch

from local_newsifier.services.entity_service import EntityService
from local_newsifier.models.entity import Entity

@pytest.fixture
def mock_entity_service_deps():
    """Create mock dependencies for EntityService."""
    mock_entity_crud = Mock()
    mock_canonical_entity_crud = Mock()
    mock_session = Mock()
    
    # Create a test entity
    test_entity = Entity(id=1, name="Test Entity", type="PERSON")
    mock_entity_crud.get.return_value = test_entity
    
    return {
        "entity_crud": mock_entity_crud,
        "canonical_entity_crud": mock_canonical_entity_crud,
        "session": mock_session,
        "test_entity": test_entity
    }

def test_entity_service_get_entity(mock_entity_service_deps):
    """Test EntityService.get_entity method."""
    # Arrange
    deps = mock_entity_service_deps
    service = EntityService(
        entity_crud=deps["entity_crud"],
        canonical_entity_crud=deps["canonical_entity_crud"],
        session=deps["session"]
    )
    
    # Act
    entity = service.get_entity(1)
    
    # Assert
    deps["entity_crud"].get.assert_called_once_with(deps["session"], id=1)
    assert entity == deps["test_entity"]
```

### Integration Testing

For integration tests involving multiple components:

1. **Mock External Dependencies** - Mock database connections, APIs, etc.
2. **Use Real Components** - Let internal components interact with each other
3. **Verify End-to-End Workflow** - Verify the complete workflow

#### Example: Integration Test for Entity Tracking Flow

```python
import pytest
from unittest.mock import Mock, patch

from local_newsifier.flows.entity_tracking_flow import EntityTrackingFlow
from local_newsifier.models.article import Article

@pytest.fixture
def mock_tracking_flow_deps():
    """Create mock dependencies for EntityTrackingFlow."""
    # Create mock services and tools
    mock_entity_service = Mock()
    mock_entity_tracker = Mock()
    mock_entity_resolver = Mock()
    
    # Configure mock behaviors
    mock_entity_tracker.extract_entities.return_value = [
        {"text": "John Doe", "type": "PERSON"},
        {"text": "New York", "type": "LOCATION"}
    ]
    
    return {
        "entity_service": mock_entity_service,
        "entity_tracker": mock_entity_tracker,
        "entity_resolver": mock_entity_resolver
    }

def test_entity_tracking_flow(mock_tracking_flow_deps):
    """Test entity tracking flow end-to-end."""
    # Arrange
    deps = mock_tracking_flow_deps
    flow = EntityTrackingFlow(
        entity_service=deps["entity_service"],
        entity_tracker=deps["entity_tracker"],
        entity_resolver=deps["entity_resolver"]
    )
    
    # Create a test article
    article = Article(id=1, title="Test Article", content="John Doe visited New York")
    
    # Act
    result = flow.track_entities_in_article(article.id)
    
    # Assert
    deps["entity_tracker"].extract_entities.assert_called_once()
    assert len(result["tracked_entities"]) == 2
```

### Mocking Strategies

#### Strategy 1: Using Pytest Monkeypatch to Mock Provider Functions

```python
@pytest.fixture
def patch_injectable_dependencies(monkeypatch):
    """Patch injectable dependencies for tests."""
    # Create mocks
    mock_entity_crud = Mock()
    mock_session = Mock()
    
    # Patch provider functions
    monkeypatch.setattr("local_newsifier.di.providers.get_entity_crud", lambda: mock_entity_crud)
    monkeypatch.setattr("local_newsifier.di.providers.get_session", lambda: mock_session)
    
    return {
        "entity_crud": mock_entity_crud,
        "session": mock_session
    }

def test_with_patched_dependencies(patch_injectable_dependencies):
    """Test using patched dependencies."""
    # Mock dependencies are available in the fixture
    deps = patch_injectable_dependencies
    
    # Now any component using these provider functions will get the mocks
    result = some_function_using_injectable_components()
    
    # Assert using the mocks
    deps["entity_crud"].get.assert_called_once()
```

#### Strategy 2: Direct Instantiation

```python
def test_with_direct_instantiation():
    """Test using direct instantiation with mock dependencies."""
    # Create mock dependencies
    mock_entity_crud = Mock()
    mock_session = Mock()
    
    # Create the service directly with mocks
    service = EntityService(
        entity_crud=mock_entity_crud,
        session=mock_session,
        canonical_entity_crud=Mock()
    )
    
    # Test the service
    service.get_entity(1)
    
    # Assert
    mock_entity_crud.get.assert_called_once_with(mock_session, id=1)
```

## Handling Circular Dependencies

Circular dependencies occur when two components depend on each other. Here are strategies to handle them:

### Strategy 1: Factory Provider Functions

```python
@injectable(use_cache=False)
def get_service_a():
    """Provider for ServiceA that handles circular dependency."""
    from local_newsifier.services.service_b import ServiceB
    from local_newsifier.di.providers import get_service_b
    
    # Get ServiceB lazily to break the circular dependency
    service_b = get_service_b()
    
    from local_newsifier.services.service_a import ServiceA
    return ServiceA(service_b=service_b)
```

### Strategy 2: Dependency Injection in Methods

```python
@injectable(use_cache=False)
class ServiceA:
    def __init__(self):
        """Initialize without circular dependencies."""
        pass
    
    def method_needing_service_b(
        self,
        service_b: Annotated[ServiceB, Depends(get_service_b)]
    ):
        """Method that uses ServiceB, injected at method level."""
        return service_b.do_something()
```

### Strategy 3: Interface Segregation

Break the components into smaller, more focused ones to eliminate circular dependencies.

## Troubleshooting

### Common Issues

#### Issue 1: "No provider found for dependency"

**Symptoms**: Error when injecting a dependency, stating no provider was found.

**Solution**:
1. Check that the provider function exists in `di/providers.py`
2. Verify the import path in your provider function
3. Check for typos in the dependency name

#### Issue 2: "Instance is not bound to a Session"

**Symptoms**: SQLModel objects being used after their session is closed.

**Solution**:
1. Don't pass SQLModel objects between sessions
2. Use IDs instead of objects when crossing session boundaries
3. Ensure session is properly managed in provider functions
4. Make sure to use `use_cache=False` for database-interacting components

#### Issue 3: Asyncio Event Loop Errors

**Symptoms**:
- "Event loop is closed" errors
- "No running event loop" errors

**Solution**:
1. Use the appropriate event loop fixture in tests
2. Ensure the event loop is properly managed in tests
3. Add and use the `event_loop_fixture` in test functions

```python
@pytest.mark.asyncio
async def test_async_function(event_loop_fixture):
    """Test an async function with proper event loop fixture."""
    # Test implementation
```

## Event Loop Handling in Tests

When testing components that use the `@injectable` decorator, you may encounter asyncio event loop related errors. This is because fastapi-injectable uses asyncio under the hood for dependency resolution, even in synchronous code.

### Common Event Loop Issues

1. **"Event loop is closed" Errors**

   This happens when a test uses an event loop that was already closed, often due to setup/teardown ordering issues.

2. **"No running event loop in thread" Errors**

   This occurs when fastapi-injectable tries to use an event loop that doesn't exist in the current thread.

3. **Invalid Type Errors with SQLModel Session**

   FastAPI's dependency injection may try to handle SQLModel's Session as a Pydantic field, which doesn't work properly in test environments.

### The Conditional Decorator Pattern

To avoid event loop issues, use the "Conditional Decorator Pattern" - applying the `@injectable` decorator conditionally based on the execution environment:

```python
# First define your class normally
class OpinionVisualizerTool:
    """Tool for generating visualizations of sentiment and opinion data."""

    def __init__(self, session: Optional[Session] = None):
        self.session = session

    # ... rest of the class implementation ...

# Then apply the decorator conditionally at the end of the file
try:
    # Only apply in non-test environments
    if not os.environ.get('PYTEST_CURRENT_TEST'):
        from fastapi_injectable import injectable
        OpinionVisualizerTool = injectable(use_cache=False)(OpinionVisualizerTool)
except (ImportError, Exception):
    pass
```

### Implementing the Conditional Decorator Pattern

Follow these steps to implement this pattern:

1. **Define your class normally** without applying the decorator directly
   ```python
   class MyTool:
       def __init__(self, session: Optional[Session] = None):
           self.session = session
   ```

2. **Apply the decorator conditionally** at the end of your file
   ```python
   try:
       # Only apply in non-test environments
       if not os.environ.get('PYTEST_CURRENT_TEST'):
           from fastapi_injectable import injectable
           MyTool = injectable(use_cache=False)(MyTool)
   except (ImportError, Exception):
       pass
   ```

### Properly Using the event_loop_fixture

Always include the `event_loop_fixture` in tests that interact with injectable components:

```python
def test_with_injectable_component(event_loop_fixture):
    """Test that interacts with an injectable component."""
    # Create the component directly to bypass dependency injection
    component = MyComponent(session=Mock(), other_dependency=Mock())

    # Test the component
    result = component.process()
    assert result == expected_value
```

For components that absolutely require dependency injection in tests:

```python
@pytest.mark.asyncio
async def test_with_injected_component(event_loop_fixture, injectable_service_fixture):
    """Test that uses the injectable service fixture."""
    # Get the service using the fixture
    service = injectable_service_fixture(get_my_service)

    # Test the service
    result = service.process()
    assert result == expected_value
```

### Testing Strategy for Injectable Components

1. **Prefer Direct Instantiation**: When possible, instantiate components directly with mock dependencies
   ```python
   # Direct instantiation bypasses dependency injection entirely
   service = MyService(
       dependency1=mock_dependency1,
       dependency2=mock_dependency2
   )
   ```

2. **Use CI Skip for Problematic Tests**: For tests that can't avoid event loop issues, use the CI skip decorator
   ```python
   from tests.ci_skip_config import ci_skip_injectable

   @ci_skip_injectable
   def test_problematic_injectable(event_loop_fixture):
       # Test implementation
   ```

3. **Create Separate Test Files**: Keep tests that require event loops in separate files from those that don't
   ```
   test_component.py         # Direct instantiation tests (no event loop needed)
   test_component_inject.py  # Tests that use dependency injection (needs event loop)
   ```

### Complete Example: Implementing and Testing a Tool with the Conditional Decorator Pattern

Here's a complete example of implementing a tool using the conditional decorator pattern:

**File: src/local_newsifier/tools/my_analyzer.py**
```python
import os
import logging
from typing import Optional, List, Dict, Any, TYPE_CHECKING

from sqlmodel import Session

if TYPE_CHECKING:
    # Import types only for type checking
    from fastapi_injectable import injectable
else:
    # Runtime imports
    pass

logger = logging.getLogger(__name__)

class MyAnalyzerTool:
    """Tool for analyzing data."""

    def __init__(self, session: Optional[Session] = None):
        """Initialize with optional dependencies."""
        self.session = session

    def analyze_data(self, data: Dict[str, Any], *, session: Optional[Session] = None) -> List[Dict]:
        """Analyze the provided data.

        Args:
            data: The data to analyze
            session: Optional session override

        Returns:
            Analysis results
        """
        # Use provided session or instance session
        session = session or self.session

        # Analysis implementation...
        results = []

        # Return results
        return results

# Apply injectable decorator conditionally to avoid test issues
try:
    # Only apply in non-test environments
    if not os.environ.get('PYTEST_CURRENT_TEST'):
        from fastapi_injectable import injectable
        MyAnalyzerTool = injectable(use_cache=False)(MyAnalyzerTool)
except (ImportError, Exception):
    pass
```

**File: tests/tools/test_my_analyzer.py**
```python
import pytest
from unittest.mock import Mock, patch

from tests.fixtures.event_loop import event_loop_fixture
from tests.ci_skip_config import ci_skip_injectable

from local_newsifier.tools.my_analyzer import MyAnalyzerTool

# Regular tests using direct instantiation
class TestMyAnalyzerTool:
    @pytest.fixture
    def mock_session(self):
        return Mock()

    @pytest.fixture
    def analyzer(self, mock_session):
        return MyAnalyzerTool(session=mock_session)

    def test_analyze_data(self, analyzer, mock_session):
        # Test using direct instantiation
        test_data = {"key": "value"}
        results = analyzer.analyze_data(test_data)

        # Assertions...
        assert isinstance(results, list)

# Injectable-specific tests that might have event loop issues
@ci_skip_injectable
class TestMyAnalyzerToolInjectable:
    @pytest.fixture
    def mock_session(self):
        return Mock()

    def test_with_session_override(self, mock_session, event_loop_fixture):
        """Test providing a session override at call time."""
        analyzer = MyAnalyzerTool()
        analyzer.analyze_data({"key": "value"}, session=mock_session)
```

### Performance Considerations

1. **Session Management**: Avoid carrying SQLModel objects between sessions
2. **Caching Decisions**: We use `use_cache=False` for safety, but be aware of increased object creation
3. **Lazy Imports**: Use lazy imports to prevent circular imports and improve startup time

### Debugging Dependency Resolution

1. **Enable Logging**: Increase logging level to see dependency resolution

```python
import logging
logging.getLogger("fastapi_injectable").setLevel(logging.DEBUG)
```

2. **Provider Troubleshooting**: Add print statements in provider functions to track execution

3. **Dependency Tracing**: Create a debugging provider that logs calls

```python
@injectable(use_cache=False)
def get_debug_entity_service(
    entity_crud: Annotated[EntityCRUD, Depends(get_entity_crud)],
    session: Annotated[Session, Depends(get_session)],
):
    """Debug provider for EntityService."""
    print(f"Creating EntityService with {entity_crud} and {session}")
    from local_newsifier.services.entity_service import EntityService
    return EntityService(entity_crud=entity_crud, session=session)
```