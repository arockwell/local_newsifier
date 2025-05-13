# Dependency Injection Anti-Patterns

This document identifies common anti-patterns related to dependency injection in the Local Newsifier codebase, particularly as we migrate from the legacy DIContainer to fastapi-injectable.

## Identified Anti-Patterns

### 1. Global Instantiation of Injectable Classes

**Anti-pattern:** Instantiating classes decorated with `@injectable` at module level.

```python
# BAD PRACTICE
@injectable(use_cache=False)
class RSSParser:
    # ...

# Global instance created at module import time
_parser = RSSParser()  # This triggers injectable dependency resolution during import!
```

**Why it's problematic:**
- Causes `RuntimeError: this event loop is already running` when the module is imported in an async context
- Triggers dependency resolution before the application is properly initialized
- Can lead to circular import issues
- Can create race conditions during application startup

**Correct approach:**
- Use provider functions to create instances when needed
- Access injectable components through the DI system, not through global variables

```python
# GOOD PRACTICE
@injectable(use_cache=False)
class RSSParser:
    # ...

# In providers.py
@injectable(use_cache=False)
def get_rss_parser():
    return RSSParser()
    
# In code that needs an RSSParser
from local_newsifier.di.providers import get_rss_parser
parser = get_rss_parser()
```

### 2. Mixing Dependency Access Patterns

**Anti-pattern:** Inconsistent access to dependencies, mixing direct imports, global instances, and proper DI.

```python
# BAD PRACTICE
# In one file
from local_newsifier.tools.specific_implementation import SpecificImplementation
result = SpecificImplementation().process()

# In another file
from local_newsifier.di.providers import get_implementation
result = get_implementation().process()
```

**Why it's problematic:**
- Creates inconsistent dependency management
- Makes testing harder by mixing different instantiation patterns
- Can bypass intended lifecycle management
- Leads to unexpected behavior with stateful components

**Correct approach:**
- Always use the same DI pattern to access a specific dependency
- Prefer dependency injection over direct imports of implementation classes

```python
# GOOD PRACTICE
# Consistent use of DI
from local_newsifier.di.providers import get_implementation
result = get_implementation().process()
```

### 3. Synchronous Code in Async Contexts

**Anti-pattern:** Running synchronous code that triggers async operations at module level.

```python
# BAD PRACTICE
# At module level
async_thing = AsyncThing()  # This might internally trigger async operations
```

**Why it's problematic:**
- Can trigger `RuntimeError: this event loop is already running` errors
- May cause deadlocks or race conditions
- Can break application startup sequences

**Correct approach:**
- Defer instantiation of components with async behavior
- Use proper async initialization patterns
- Keep module-level code simple and purely synchronous

```python
# GOOD PRACTICE
async def get_async_thing():
    if not hasattr(get_async_thing, "_instance"):
        get_async_thing._instance = await AsyncThing.create()
    return get_async_thing._instance
```

### 4. Hidden Dependencies

**Anti-pattern:** Components that secretly fetch their own dependencies instead of having them injected.

```python
# BAD PRACTICE
class ServiceWithHiddenDependencies:
    def __init__(self):
        # Hidden dependency fetched internally
        from local_newsifier.container import container
        self.dependency = container.get("some_dependency")
```

**Why it's problematic:**
- Makes testing difficult without complex mocking
- Creates hidden coupling between components
- Can lead to unexpected behavior when dependencies change
- Breaks the explicit dependency principle

**Correct approach:**
- Make all dependencies explicit in constructor
- Use dependency injection consistently

```python
# GOOD PRACTICE
@injectable(use_cache=False)
class ServiceWithExplicitDependencies:
    def __init__(self, dependency: SomeDependency):
        self.dependency = dependency
```

### 5. Inappropriate Singleton Usage

**Anti-pattern:** Using singletons (or `use_cache=True`) for stateful components.

```python
# BAD PRACTICE
@injectable(use_cache=True)  # Equivalent to singleton in fastapi-injectable 0.7.0
class StatefulService:
    def __init__(self):
        self.state = {}
        
    def process(self, item):
        # Modifies internal state
        self.state[item.id] = item
```

**Why it's problematic:**
- Shared state can lead to data leakage between requests
- Can create concurrency issues
- Makes testing unpredictable
- Can cause hard-to-debug errors

**Correct approach:**
- Use `use_cache=False` for stateful components
- Only use singletons for truly stateless, immutable components

```python
# GOOD PRACTICE
@injectable(use_cache=False)  # New instance for each injection
class StatefulService:
    def __init__(self):
        self.state = {}
```

### 6. Import-Time Side Effects

**Anti-pattern:** Code that performs significant work at import time.

```python
# BAD PRACTICE
# At module level
print("Initializing expensive resources...")
database = Database.connect()
model = load_large_model()
```

**Why it's problematic:**
- Can slow down application startup
- Executes before error handling is in place
- Can cause problems with testing
- May trigger unexpected behavior during imports

**Correct approach:**
- Lazy initialization
- Use factories or providers 
- Defer expensive operations to runtime

```python
# GOOD PRACTICE
def get_model():
    if not hasattr(get_model, "_model"):
        get_model._model = load_large_model()
    return get_model._model
```

### 7. Circular Dependencies

**Anti-pattern:** Components that depend on each other directly or indirectly.

```python
# BAD PRACTICE
# In service_a.py
@injectable(use_cache=False)
class ServiceA:
    def __init__(self, service_b: "ServiceB"):
        self.service_b = service_b

# In service_b.py
@injectable(use_cache=False)
class ServiceB:
    def __init__(self, service_a: "ServiceA"):
        self.service_a = service_a
```

**Why it's problematic:**
- Can create deadlocks in DI resolution
- Makes the code harder to understand
- Often indicates poor separation of concerns
- Can cause import-time errors

**Correct approach:**
- Refactor to remove circular dependencies
- Introduce an intermediate service
- Use runtime imports
- Pass functions instead of instances

```python
# GOOD PRACTICE
# Refactored to remove circular dependency
@injectable(use_cache=False)
class ServiceC:  # Intermediate service with common functionality
    pass

@injectable(use_cache=False)
class ServiceA:
    def __init__(self, service_c: ServiceC):
        self.service_c = service_c
        
@injectable(use_cache=False)
class ServiceB:
    def __init__(self, service_c: ServiceC):
        self.service_c = service_c
```

## Best Practices for Dependency Injection

### 1. Prefer Constructor Injection

Always pass dependencies through constructors rather than fetching them internally:

```python
# GOOD PRACTICE
@injectable(use_cache=False)
class Service:
    def __init__(self, dependency: Dependency):
        self.dependency = dependency
```

### 2. Use Consistent Scope Management

Use appropriate scopes for different types of components:

- `use_cache=False` (default choice): For most components, especially those interacting with databases
- `use_cache=True`: Only for completely stateless, thread-safe utilities (use with extreme caution)

### 3. Make Dependencies Explicit

Always make dependencies explicit in type annotations:

```python
# GOOD PRACTICE
@injectable(use_cache=False)
def get_service(
    dependency_a: Annotated[DependencyA, Depends(get_dependency_a)],
    dependency_b: Annotated[DependencyB, Depends(get_dependency_b)]
):
    return Service(dependency_a, dependency_b)
```

### 4. Lazy Initialization

Use lazy initialization for expensive resources:

```python
# GOOD PRACTICE
def get_expensive_resource():
    if not hasattr(get_expensive_resource, "_instance"):
        get_expensive_resource._instance = create_expensive_resource()
    return get_expensive_resource._instance
```

### 5. Maintain Clean Module Boundaries

Don't let implementation details leak between modules:

```python
# GOOD PRACTICE
# Public API in __init__.py
from .implementation import public_function

# Hide implementation details
__all__ = ["public_function"]
```

## How to Identify Potential Issues

When reviewing code, look for these warning signs:

1. Classes decorated with `@injectable` that are instantiated directly
2. Global variables that hold complex objects
3. Import statements that might trigger side effects
4. Dependencies fetched inside methods rather than injected
5. Stateful classes marked with `use_cache=True`
6. Complex code executed at module level
7. Multiple different ways to access the same dependency

## Converting Legacy Code

When migrating from the old container to fastapi-injectable:

1. Create provider functions in `di/providers.py` with appropriate scope
2. Update code to use these providers instead of direct instantiation
3. Ensure all dependencies are explicitly injected
4. Test thoroughly to catch any circular dependencies
5. Fix import ordering issues to avoid problems with module-level code