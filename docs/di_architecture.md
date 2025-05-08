# Dependency Injection Architecture

## Overview

Local Newsifier is currently in transition between two dependency injection (DI) systems:

1. **Custom DIContainer**: A homegrown DI container implementation that was the original solution
2. **fastapi-injectable**: A third-party framework leveraging FastAPI's dependency injection patterns

This document explains the architecture of both systems, their relationship, and provides guidance for developers during this transition period.

## Architecture Overview

```
┌────────────────────────────────┐      ┌─────────────────────────────────┐
│       DIContainer System       │      │     fastapi-injectable System    │
│                                │      │                                  │
│ ┌──────────┐    ┌────────────┐ │      │ ┌─────────────┐  ┌────────────┐ │
│ │   DI     │    │ Component  │ │      │ │  Injectable │  │ Component  │ │
│ │Container │◄───┤  Factory   │ │      │ │  Component  │◄─┤  Provider  │ │
│ └──────────┘    └────────────┘ │      │ └─────────────┘  └────────────┘ │
└──────────────┬─────────────────┘      └────────────┬────────────────────┘
               │                                     │
               │         ┌──────────────────┐        │
               └────────►│  Adapter Layer   │◄───────┘
                         │                  │
                         └──────────────────┘
```

### Custom DIContainer System

The original DI system (`di_container.py`) provides:

- Service registration and resolution
- Factory methods for lazy loading
- Parameterized factories
- Service lifetime management
- Circular dependency resolution

### fastapi-injectable System

The newer system based on `fastapi-injectable` offers:

- Integration with FastAPI's dependency injection system
- Type-safe dependency injection with `Annotated` types
- Consistent `Depends()` pattern throughout the codebase
- Improved testing capabilities

### Adapter Layer

The adapter (`fastapi_injectable_adapter.py`) bridges between the two systems, allowing:

- Gradual migration from DIContainer to fastapi-injectable
- Registration of DIContainer services with fastapi-injectable
- Parameterized service resolution
- Appropriate service lifetime handling

## Current Status

- Both systems are actively used in the codebase
- New API endpoints primarily use fastapi-injectable
- Most services, flows, and tools still use DIContainer
- The adapter allows components to get services from either system

## Migration Strategy

The project is following a phased approach to migrate from DIContainer to fastapi-injectable:

### Phase 1: Foundation (Completed)
- Set up fastapi-injectable infrastructure
- Create adapter layer for compatibility
- Implement initial provider functions

### Phase 2: Gradual Migration (Current)
- Migrate components incrementally
- Keep both systems operational
- Adapt tests for the new pattern

### Phase 3: Complete Migration (Planned)
- Fully transition all components
- Remove legacy DIContainer
- Standardize on fastapi-injectable patterns

## Decision Tree for Developers

When working on DI-related code, use this decision tree to determine the appropriate approach:

```
Is this a new component?
├── Yes → Use fastapi-injectable
│   ├── Is it a service with database interaction?
│   │   ├── Yes → Use @injectable(use_cache=False)
│   │   └── No → Consider @injectable with appropriate caching
│   └── Does it need to interact with DIContainer components?
│       ├── Yes → Use the adapter
│       └── No → Use pure fastapi-injectable approach
└── No → Is it tightly coupled with other DIContainer components?
    ├── Yes → Keep using DIContainer for now
    │   └── Add to migration backlog
    └── No → Consider migrating to fastapi-injectable
```

## Related Documentation

- [Injectable Patterns Guide](injectable_patterns.md) - Comprehensive examples and patterns for all component types
- [Original DIContainer Documentation](dependency_injection.md) - Legacy DIContainer documentation
- [fastapi-injectable Migration Guide](fastapi_injectable.md) - Migration process overview
- [Issue #151: Evaluate Migration to fastapi-injectable](https://github.com/arockwell/local_newsifier/issues/151) - Original evaluation issue

## Testing Strategies

Testing components with different DI systems requires different approaches. Here's how to test components based on their DI implementation:

### Testing DIContainer Components

Components that use DIContainer can be tested by creating a test-specific container:

```python
import pytest
from unittest.mock import MagicMock
from local_newsifier.di_container import DIContainer

@pytest.fixture
def test_container():
    """Create a container with mock services for testing."""
    container = DIContainer()
    
    # Register mock services
    mock_entity_service = MagicMock()
    mock_article_service = MagicMock()
    
    container.register("entity_service", mock_entity_service)
    container.register("article_service", mock_article_service)
    
    return container, {
        "entity_service": mock_entity_service,
        "article_service": mock_article_service
    }

def test_flow_with_container(test_container):
    """Test a flow that uses DIContainer."""
    container, mocks = test_container
    
    # Create component with test container
    flow = EntityTrackingFlow(container=container)
    
    # Test interactions
    flow.process_entity("test_entity")
    
    # Verify mock was called correctly
    mocks["entity_service"].get_entity.assert_called_once_with("test_entity")
```

### Testing fastapi-injectable Components

Components using fastapi-injectable can be tested by mocking the provider functions:

```python
import pytest
from unittest.mock import MagicMock, patch
from local_newsifier.services.injectable_entity_service import InjectableEntityService

@pytest.fixture
def mock_injectable_dependencies(monkeypatch):
    """Mock dependencies for injectable components."""
    # Create mocks
    mock_entity_crud = MagicMock()
    mock_session = MagicMock()
    
    # Patch provider functions
    monkeypatch.setattr("local_newsifier.di.providers.get_entity_crud", lambda: mock_entity_crud)
    monkeypatch.setattr("local_newsifier.di.providers.get_session", lambda: mock_session)
    
    return {
        "entity_crud": mock_entity_crud,
        "session": mock_session
    }

def test_injectable_service(mock_injectable_dependencies):
    """Test a service using fastapi-injectable."""
    mocks = mock_injectable_dependencies
    
    # Create service directly with mocked dependencies
    service = InjectableEntityService(
        entity_crud=mocks["entity_crud"],
        session=mocks["session"]
    )
    
    # Test the service
    service.get_entity(1)
    
    # Verify interactions
    mocks["entity_crud"].get.assert_called_once_with(mocks["session"], id=1)
```

### Testing Components Using Both Systems

For components that interact with both DI systems through the adapter:

```python
import pytest
from unittest.mock import MagicMock, patch
from local_newsifier.di_container import DIContainer

@pytest.fixture
def hybrid_test_environment(monkeypatch):
    """Create a test environment that supports both DI systems."""
    # Setup DIContainer
    container = DIContainer()
    mock_container_service = MagicMock()
    container.register("legacy_service", mock_container_service)
    
    # Setup injectable mocks
    mock_injectable_service = MagicMock()
    monkeypatch.setattr("local_newsifier.di.providers.get_injectable_service", 
                       lambda: mock_injectable_service)
    
    # Patch adapter to use test container
    monkeypatch.setattr("local_newsifier.fastapi_injectable_adapter.di_container", container)
    
    return {
        "container": container,
        "legacy_service": mock_container_service,
        "injectable_service": mock_injectable_service
    }

def test_hybrid_component(hybrid_test_environment):
    """Test a component that uses both DI systems."""
    mocks = hybrid_test_environment
    
    # Test component that might use the adapter or both systems
    # ...

    # Verify interactions with both systems
    mocks["legacy_service"].some_method.assert_called_once()
    mocks["injectable_service"].other_method.assert_called_once()
```

## Component Migration Guide

This section provides guidance for migrating different component types from DIContainer to fastapi-injectable.

### Service Migration

Services are typically stateful components that perform business logic and may interact with the database.

**Original DIContainer Version:**
```python
class EntityService:
    def __init__(self, entity_crud=None, session_factory=None):
        from local_newsifier.container import container
        self.entity_crud = entity_crud or container.get("entity_crud")
        self.session_factory = session_factory or container.get("session_factory")
```

**Migrated fastapi-injectable Version:**
```python
from typing import Annotated
from fastapi import Depends
from fastapi_injectable import injectable
from sqlmodel import Session

@injectable(use_cache=False)  # Don't cache services with database interaction
class InjectableEntityService:
    def __init__(
        self,
        entity_crud: Annotated[EntityCRUD, Depends(get_entity_crud)],
        session: Annotated[Session, Depends(get_session)]
    ):
        self.entity_crud = entity_crud
        self.session = session
```

### Flow Migration

Flows orchestrate multiple services and typically contain business process logic.

**Original DIContainer Version:**
```python
class EntityTrackingFlow:
    def __init__(self, container=None):
        from local_newsifier.container import container as default_container
        self.container = container or default_container
        self.entity_service = self.container.get("entity_service")
        self.article_service = self.container.get("article_service")
```

**Migrated fastapi-injectable Version:**
```python
from typing import Annotated
from fastapi import Depends
from fastapi_injectable import injectable

@injectable(use_cache=False)
class InjectableEntityTrackingFlow:
    def __init__(
        self,
        entity_service: Annotated[EntityService, Depends(get_entity_service)],
        article_service: Annotated[ArticleService, Depends(get_article_service)]
    ):
        self.entity_service = entity_service
        self.article_service = article_service
```

### Tool Migration

Tools provide utility functions and are generally more stateless.

**Original DIContainer Version:**
```python
class EntityExtractor:
    def __init__(self, nlp_model=None):
        from local_newsifier.container import container
        self.nlp_model = nlp_model or container.get("nlp_model")
```

**Migrated fastapi-injectable Version:**
```python
from typing import Annotated
from fastapi import Depends
from fastapi_injectable import injectable

@injectable(use_cache=True)  # Can cache stateless tools
class InjectableEntityExtractor:
    def __init__(
        self,
        nlp_model: Annotated[NLPModel, Depends(get_nlp_model)]
    ):
        self.nlp_model = nlp_model
```

## Migration Timeline

The migration from DIContainer to fastapi-injectable is planned to proceed in these phases:

| Phase | Status | Estimated Completion | Components |
|-------|--------|----------------------|------------|
| Foundation | Complete | Q1 2025 | Basic infrastructure, adapter layer |
| Core Services | In Progress | Q2 2025 | Entity service, Article service |
| Flow Classes | Not Started | Q3 2025 | EntityTrackingFlow, NewsPipelineFlow |
| Tools | Not Started | Q3 2025 | All analysis and extraction tools |
| API Integration | In Progress | Q2 2025 | Remaining API endpoints |
| CLI Commands | Not Started | Q4 2025 | All CLI commands |
| Task System | Not Started | Q4 2025 | Celery tasks and background processing |
| Legacy Removal | Not Started | Q1 2026 | Remove DIContainer completely |

## Best Practices and Anti-patterns

### Best Practices

1. **Consistent Dependency Declaration**
   - Use `Annotated[Type, Depends()]` for all dependencies
   - Declare all dependencies in constructor parameters

2. **Clear Caching Decisions**
   - Use `use_cache=False` for stateful components
   - Only use `use_cache=True` for truly stateless utilities

3. **Proper Error Handling**
   - Handle missing dependencies gracefully
   - Provide meaningful error messages when dependencies can't be resolved

4. **Migration Tracking**
   - Keep track of migrated components
   - Document components that still need migration

### Anti-patterns

1. **Mixing DI Systems Directly**
   - ❌ Don't use container.get() in a class that uses @injectable
   - ✅ Use the adapter if you need to interact with both systems

2. **Inconsistent Service Lifetimes**
   - ❌ Don't use `use_cache=True` for database-interacting services
   - ✅ Be consistent with stateful vs stateless component caching

3. **Hidden Dependencies**
   - ❌ Don't import dependencies inside methods
   - ✅ Declare all dependencies in constructor parameters

4. **Circular Dependencies**
   - ❌ Don't create mutual dependencies between services
   - ✅ Use provider functions or refactor component responsibilities