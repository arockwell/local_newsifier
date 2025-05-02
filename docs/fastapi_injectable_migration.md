# FastAPI-Injectable Migration Plan

## Research and Analysis

### Initial Findings

1. **Dependency Conflict**:
   - Local Newsifier uses FastAPI 0.110.0
   - fastapi-injectable requires FastAPI >=0.112.4
   - This will require updating the FastAPI version

2. **Current DI System**:
   - Custom `DIContainer` in `src/local_newsifier/di_container.py`
   - Container singleton in `src/local_newsifier/container.py`
   - FastAPI dependencies in `src/local_newsifier/api/dependencies.py`
   - Services registered with factory methods

3. **API Integration**:
   - Current endpoints use `Depends(get_session)` and similar dependency functions
   - Session management is handled via a session factory from the container
   - Services are retrieved from the container in dependency functions

### About fastapi-injectable

fastapi-injectable is a dependency injection library for FastAPI that:

- Uses decorators to mark injectable components
- Provides scoped lifetimes (singleton, transient, request)
- Supports auto-discovery of injectable components
- Integrates directly with FastAPI's dependency system
- Handles circular dependencies

### Key Differences

| Feature | Current DIContainer | fastapi-injectable |
|---------|---------------------|-------------------|
| Registration | Explicit registration with container.register() | Decorator-based (@injectable) |
| Resolution | container.get("service_name") | Direct injection via type hints |
| Scopes | SINGLETON, TRANSIENT, SCOPED | SINGLETON, TRANSIENT, REQUEST |
| Integration | Manual integration with FastAPI dependencies | Direct FastAPI integration |
| Discovery | Manual registration | Auto-discovery with scanning |

## Migration Strategy

### 1. Update Dependencies

- Update FastAPI to required version (>=0.112.4)
- Add fastapi-injectable
- Test core application functionality after updates

### 2. Create Adapter Layer

- Create an adapter pattern to bridge between systems during migration
- Allow both DI systems to coexist during transition
- Gradually migrate components from DIContainer to fastapi-injectable

### 3. Injectable Service Pattern

Convert services to use the injectable pattern:

```python
from fastapi_injectable import injectable, Scope

@injectable(scope=Scope.SINGLETON)
class EntityService:
    def __init__(self, entity_crud: EntityCRUD, session_factory: SessionFactory):
        self.entity_crud = entity_crud
        self.session_factory = session_factory
```

### 4. Update API Dependencies

Replace current dependency functions with injectable versions:

```python
# Current approach
def get_article_service() -> ArticleService:
    return container.get("article_service")

# New approach with fastapi-injectable
from fastapi_injectable import Inject

def get_article_service(service: ArticleService = Inject()):
    return service
```

### 5. Session Management Updates

Update session management to use fastapi-injectable's request scope:

```python
@injectable(scope=Scope.REQUEST)
class RequestSession:
    def __init__(self, session_factory: SessionFactory):
        self.session = session_factory()
        
    def __del__(self):
        if self.session:
            self.session.close()
```

### 6. CRUD Modules Conversion

Convert CRUD modules to use injectable pattern:

```python
@injectable(scope=Scope.SINGLETON)
class EntityCRUD:
    def get(self, session: Session, id: int):
        # Implementation
```

### 7. Container Initialization

Update application startup to use fastapi-injectable initialization:

```python
from fastapi_injectable import InjectableAPI, load_modules

app = InjectableAPI()
load_modules(["local_newsifier.services", "local_newsifier.crud"])
```

## Compatibility Challenges

- Current code references container directly in some places
- State-based flows may need special handling
- CLI commands use container directly
- Celery tasks use container for service resolution

## Testing Strategy

- Create tests for both DI systems working together
- Verify services can be resolved through both mechanisms
- Test FastAPI endpoints with new DI system
- Ensure CLI commands continue working during transition