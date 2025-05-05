# Tool Registration and Dependency Injection Patterns

This document provides guidelines for registering tool classes in the dependency injection container and using them consistently throughout the application.

## Overview

All tool classes are registered in the dependency injection container to provide:
- Centralized management of tool instances
- Consistent access patterns
- Configurable initialization

Tools are organized into three main categories:
1. **Core Tools** - Basic utilities like web scraping and file handling
2. **Analysis Tools** - Specialized analysis functionality like trend analysis
3. **Entity Tools** - Entity extraction, resolution, and tracking

## Naming Conventions

Tools registered in the container follow this naming pattern:
- Standard name: `{tool_name}_tool` (e.g., `web_scraper_tool`)
- Legacy name: `{tool_name}` (for backward compatibility)

## Core Pattern: Base/Derived Classes

The primary pattern for flow components separates core functionality from dependency injection:

```python
# Base class with core logic
class EntityTrackingFlowBase:
    def __init__(self, entity_service=None, entity_tracker=None):
        self.entity_service = entity_service
        self.entity_tracker = entity_tracker
    
    def track_entities_in_article(self, article_id):
        # Core business logic implementation
        pass

# Derived class for DI integration
@injectable(use_cache=False)
class EntityTrackingFlow(EntityTrackingFlowBase):
    def __init__(
        self,
        entity_service: Annotated[EntityService, Depends(get_entity_service)],
        entity_tracker: Annotated[EntityTracker, Depends(get_entity_tracker_tool)]
    ):
        super().__init__(
            entity_service=entity_service,
            entity_tracker=entity_tracker
        )
```

## Factory Pattern for Circular Dependencies

Factory functions break circular dependencies between components:

```python
@injectable(use_cache=False)
def get_entity_service_factory() -> Callable[[], EntityService]:
    """Provide a factory function for EntityService."""
    def factory():
        from local_newsifier.di.providers import get_entity_service
        return get_entity_service()
    return factory
```

## Provider Example

For fastapi-injectable integration, use provider functions:

```python
@injectable(use_cache=False)
def get_text_summarizer_tool() -> TextSummarizerTool:
    """Provider function for TextSummarizerTool."""
    return TextSummarizerTool(max_length=100)
```