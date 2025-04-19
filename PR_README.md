# Architecture Refactoring PR

This PR introduces a new architecture for Local Newsifier that reduces tight coupling between components and implements a more Pythonic approach to dependency management and session handling.

## Key Improvements

1. **Centralized Session Management**
   - New `SessionManager` provides consistent session handling across the application
   - Eliminates inconsistent session passing between components
   - Context manager pattern for clearer transaction boundaries

2. **Service Layer**
   - New service layer encapsulates business logic
   - `EntityService` manages entity-related operations
   - Business rules are centralized rather than spread across tools and flows

3. **Dependency Injection**
   - Components accept dependencies instead of creating them
   - Improves testability with mock dependencies
   - Reduces hidden dependencies and makes data flow explicit

4. **Factory Pattern**
   - `ToolFactory` and `ServiceFactory` manage component creation
   - Consistent configuration of dependencies
   - Simplifies instantiation of complex object graphs

5. **Improved Testability**
   - Unit tests are simpler with injectable dependencies
   - See `tests/services/test_entity_service.py` for examples

## Implementation Details

### New Components

- `session_manager.py` - Improved session handling with context manager
- `services/entity_service.py` - Service for entity business logic
- `tools/entity_tracker_v2.py` - Refactored tracker using service layer
- `core/factory.py` - Factories for tool and service creation
- `flows/entity_tracking_flow_v2.py` - Refactored flow with dependency injection

### Demo

A demo script is provided to showcase the new architecture:

```bash
$ python scripts/demo_refactored_architecture.py
```

### Testing

The new architecture is much easier to test. For example:

```python
def test_entity_service():
    # Create mock dependencies
    mock_session_manager = MagicMock()
    
    # Create service with mocked dependencies
    service = EntityService(session_manager=mock_session_manager)
    
    # Test the service...
```

## Future Work

This PR lays the foundation for further refactoring. Next steps include:

1. **Additional Services**
   - Implement `SentimentService`, `TrendService`, etc.
   - Move more business logic from tools to services

2. **FastAPI Integration**
   - The new architecture is ready for API endpoints
   - Services can be directly consumed by FastAPI route handlers

3. **More Refactored Components**
   - Apply the pattern to other tools and flows
   - Gradually migrate from old to new implementations

## How to Use the New Architecture

### Creating Components

```python
# Get the session manager
session_manager = get_session_manager()

# Create services
entity_service = ServiceFactory.create_entity_service(
    session_manager=session_manager
)

# Create tools with dependencies
entity_tracker = ToolFactory.create_entity_tracker(
    session_manager=session_manager,
    entity_service=entity_service
)

# Create flows with dependencies
entity_flow = EntityTrackingFlow(
    session_manager=session_manager,
    entity_tracker=entity_tracker
)
```

### Using Session Management

```python
# Using session context manager
with session_manager.session() as session:
    # Session is automatically committed on success,
    # or rolled back on exception
    articles = article_crud.get_by_status(session, status="analyzed")
```

## Migration Strategy

The new components are implemented alongside existing ones to allow for gradual migration. The recommended approach is:

1. Start using the new SessionManager in new code
2. Create services for your domain areas
3. Refactor tools to use services
4. Update flows to use the refactored tools

This PR includes version "v2" of some components to avoid breaking existing code while introducing the new patterns.
