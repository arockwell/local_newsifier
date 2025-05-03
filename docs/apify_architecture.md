# Apify Integration Architecture

This document outlines the architectural approaches for integrating with the Apify platform in the Local Newsifier project.

## Overview

The Apify integration allows Local Newsifier to scrape web content from various sources using Apify's actors and webhooks. This document explores different architectural approaches while maintaining consistency with the project's existing patterns.

## Approach 1: Clean Architecture with SQLModel

### Core Components

#### 1. Domain Models (SQLModel-based)

```python
# Core models representing Apify concepts
class ApifySourceConfig(TableBase, table=True):
    """Configuration for an Apify data source."""
    name: str
    actor_id: str
    # ... other fields

class ApifyJob(TableBase, table=True):
    """Record of an Apify actor run."""
    source_config_id: Optional[int]
    run_id: str
    # ... other fields

class ApifyDatasetItem(TableBase, table=True):
    """Raw item from an Apify dataset."""
    job_id: int
    raw_data: Dict[str, Any]
    # ... other fields
```

#### 2. CRUD Operations

Following the project's existing CRUD pattern:

```python
class CRUDApifySourceConfig(CRUDBase[ApifySourceConfig]):
    """CRUD operations for ApifySourceConfig."""
    
    @staticmethod
    def get_active_configs(session: Session) -> List[ApifySourceConfig]:
        """Get active Apify source configurations."""
        # Implementation

class CRUDApifyJob(CRUDBase[ApifyJob]):
    """CRUD operations for ApifyJob."""
    # Methods...

class CRUDApifyDatasetItem(CRUDBase[ApifyDatasetItem]):
    """CRUD operations for ApifyDatasetItem."""
    # Methods...
```

#### 3. Client Interface (Protocol)

```python
class ApifyClientProtocol(Protocol):
    """Interface for Apify API client implementations."""
    
    def run_actor(self, actor_id: str, run_input: Dict[str, Any]) -> Dict[str, Any]:
        """Run an Apify actor with given input."""
        ...
    
    def get_dataset_items(self, dataset_id: str, **kwargs) -> List[Dict[str, Any]]:
        """Get items from an Apify dataset."""
        ...
    
    # Other methods...
```

#### 4. Service Layer

```python
class ApifyService:
    """Service for interacting with Apify."""
    
    def __init__(
        self, 
        client: ApifyClientProtocol,
        apify_source_crud = None,
        apify_job_crud = None,
        apify_dataset_item_crud = None,
        article_service = None,
        session_factory = None
    ):
        """Initialize with dependencies."""
        self.client = client
        # Get dependencies from container if not provided
        from local_newsifier.container import container
        self.apify_source_crud = apify_source_crud or container.get("apify_source_crud")
        # ... other dependencies
    
    def run_source_config(self, source_id: int) -> Dict[str, Any]:
        """Run an actor based on a stored configuration."""
        # Implementation
    
    def process_dataset_to_articles(self, dataset_id: str) -> List[int]:
        """Process dataset items into articles."""
        # Implementation
```

### Pros:
- Clear separation of concerns
- Highly testable with mock interfaces
- Consistent with clean architecture principles
- Follows existing project patterns

### Cons:
- More initial setup required
- Potential abstraction overhead
- Additional interfaces to maintain

## Approach 2: Lightweight Integration

A more direct approach with less abstraction:

```python
class ApifyService:
    """Service for interacting with Apify."""
    
    def __init__(self, token: Optional[str] = None, session_factory = None):
        """Initialize with optional token."""
        self._token = token
        self._client = None
        self._session_factory = session_factory
    
    @property
    def client(self) -> ApifyClient:
        """Get the Apify client."""
        if not self._client:
            token = self._token or settings.validate_apify_token()
            self._client = ApifyClient(token)
        return self._client
    
    def run_actor(self, actor_id: str, run_input: Dict[str, Any]) -> Dict[str, Any]:
        """Run an Apify actor."""
        return self.client.actor(actor_id).call(run_input=run_input)
    
    def get_source_config(self, source_id: int) -> ApifySourceConfig:
        """Get a source configuration."""
        with self._session_factory() as session:
            return session.get(ApifySourceConfig, source_id)
    
    def run_source_config(self, source_id: int) -> Dict[str, Any]:
        """Run a source configuration."""
        config = self.get_source_config(source_id)
        return self.run_actor(config.actor_id, config.input_configuration)
```

### Pros:
- Simpler implementation
- Less code to maintain
- Faster to implement
- More direct approach

### Cons:
- Less separation of concerns
- Harder to test
- Tighter coupling between components
- Less flexibility for changes

## Approach 3: Hybrid Approach

Combine the best of both approaches:

```python
# Use Protocol for client interface
class ApifyClientProtocol(Protocol):
    """Interface for Apify API client."""
    # Methods...

# Implement direct client adapter
class ApifyClientAdapter:
    """Adapter for Apify client."""
    # Implementation...

# Service with reduced complexity
class ApifyService:
    """Service for interacting with Apify."""
    
    def __init__(
        self, 
        client: ApifyClientProtocol,
        session_factory = None
    ):
        """Initialize with client and session factory."""
        self.client = client
        self._session_factory = session_factory
    
    def run_source_config(self, source_id: int) -> Dict[str, Any]:
        """Run a source configuration."""
        with self._session_factory() as session:
            config = session.get(ApifySourceConfig, source_id)
            return self.client.run_actor(config.actor_id, config.input_configuration)
```

### Pros:
- Balance between clean architecture and simplicity
- Key interfaces for testability
- Reduced code complexity
- Still follows project patterns

### Cons:
- Some abstraction overhead
- Partial implementation of clean architecture

## Integration with Dependency Injection

All approaches can be integrated with the project's DI container:

```python
# For the clean architecture approach
container.register_factory("apify_client", 
    lambda c: ApifyClientAdapter(token=settings.APIFY_TOKEN))

container.register_factory("apify_service", 
    lambda c: ApifyService(
        client=c.get("apify_client"),
        apify_source_crud=c.get("apify_source_crud"),
        # ... other dependencies
        session_factory=c.get("session_factory")
    ))

# For the lightweight approach
container.register_factory("apify_service", 
    lambda c: ApifyService(
        token=settings.APIFY_TOKEN,
        session_factory=c.get("session_factory")
    ))
```

## Immediate Bug Fixes Needed

Regardless of the architectural approach chosen, the following bugs need to be fixed:

### 1. 'ListPage' object is not iterable (Issue #127)

The current implementation of `get_dataset_items` attempts to iterate over a ListPage object, but it's not directly iterable:

```python
# Current implementation with bug
def get_dataset_items(self, dataset_id: str, **kwargs) -> Dict[str, Any]:
    list_page = self.client.dataset(dataset_id).list_items(**kwargs)
    return {"items": list(list_page)}  # Error here - ListPage not iterable
```

Proposed fix:

```python
def get_dataset_items(self, dataset_id: str, **kwargs) -> Dict[str, Any]:
    list_page = self.client.dataset(dataset_id).list_items(**kwargs)
    
    # Access items directly using the 'items' attribute of ListPage
    if hasattr(list_page, 'items'):
        return {"items": list_page.items}
    
    # Fall back to other approaches if needed
    elif isinstance(list_page, dict) and "items" in list_page:
        return list_page
    else:
        # Handle unexpected response format
        return {"items": [], "error": "Unexpected response format"}
```

### 2. pageFunction field error (Issue #126)

The web-scraper actor requires a pageFunction field:

```python
# Current command with missing pageFunction
nf apify run-actor apify/web-scraper --input '{"startUrls":[{"url":"https://example.com"}]}'
```

Proposed fix:

```python
# Add default pageFunction to the CLI command
@apify_group.command(name="run-actor")
@click.argument("actor_id", required=True)
@click.option("--input", "-i", help="JSON string or file path for actor input")
def run_actor(actor_id, input):
    """Run an Apify actor."""
    run_input = json.loads(input) if input else {}
    
    # Add default pageFunction for web-scraper if missing
    if actor_id == "apify/web-scraper" and "pageFunction" not in run_input:
        run_input["pageFunction"] = (
            "async function pageFunction(context) {\n"
            "  const { request, log, waitFor } = context;\n"
            "  const title = document.title;\n"
            "  const url = request.url;\n"
            "  const html = document.documentElement.outerHTML;\n"
            "  return { title, url, html };\n"
            "}"
        )
    
    # Run the actor with the enhanced input
    # ...
```

## Recommended Next Steps

1. **Fix Immediate Bugs**: Address the ListPage and pageFunction issues
2. **Start with Interface Definitions**: Define core interfaces using Protocol
3. **Enhance CRUD Operations**: Extend existing models with needed functionality
4. **Implement Client Adapter**: Create adapter with proper error handling
5. **Refactor Service Layer**: Update service to use interfaces and proper DI
6. **Update CLI and Celery**: Ensure proper integration with both

## Questions to Consider

1. How complex is the planned Apify integration? Will it evolve significantly?
2. How important is testing isolation for this module?
3. Are there performance considerations that might affect the architectural choice?
4. How does this fit with potential future DI system changes?
5. What's the priority between immediate fixes and long-term architecture?