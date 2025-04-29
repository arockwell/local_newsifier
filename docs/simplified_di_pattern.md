# Simplified Dependency Injection Pattern

This document describes the simplified dependency injection pattern implemented in the local_newsifier project to address issues with the previous approach to dependency handling in flow classes.

## Problem Statement

The previous dependency injection approach had several issues:

1. **Test Environment Detection** - Production code directly checked for pytest in `sys.modules` to determine if it was running in a test environment
2. **Special Case Logic** - Different approaches for handling tools vs. services with duplicate code
3. **Complex Initialization** - Verbose initialization with separate test and production paths
4. **Coupling to Test Implementation** - Production code was aware of testing details

## Solution

The simplified pattern provides a cleaner approach based on three core components:

1. **DependencyBase** - Base class for standardized dependency resolution
2. **Dependency** - Descriptor for declarative dependency definition
3. **FlowBase** - Flow-specific extension of DependencyBase

## Key Components

### 1. DependencyBase

```python
class DependencyBase:
    """Base class for components with dependency injection."""

    def __init__(self, container=None):
        """Initialize with optional container."""
        self.container = container
        self._dependencies = {}
        
    def _ensure_dependency(self, name, container_key=None, fallback=None):
        """Get or create a dependency."""
        # Return cached dependency if already resolved
        if name in self._dependencies:
            return self._dependencies[name]
            
        # Try to get from container
        value = None
        if self.container:
            value = self.container.get(container_key or name)
            
        # Use fallback if needed
        if value is None and fallback is not None:
            value = fallback() if callable(fallback) else fallback
            
        # Cache and return
        if value is not None:
            self._dependencies[name] = value
            
        return value

    def _register_dependency(self, name, value):
        """Register a dependency directly."""
        self._dependencies[name] = value
```

### 2. Dependency Descriptor

```python
class Dependency:
    """Descriptor for lazy dependency resolution."""
    
    def __init__(self, container_key=None, fallback=None):
        """Initialize the dependency descriptor."""
        self.name = ""  # Will be set by __set_name__
        self.container_key = container_key
        self.fallback = fallback
        
    def __set_name__(self, owner, name):
        """Set descriptor name when class is defined."""
        self.name = name
        if not self.container_key:
            # Convert attribute name to container key following project conventions
            self.container_key = name + "_tool" if name.endswith("r") else name
            
    def __get__(self, instance, owner):
        """Get dependency value, resolving if needed."""
        if instance is None:
            return self
            
        # Skip resolution during initialization if _in_init flag is set
        if hasattr(instance, '_in_init') and instance._in_init:
            return None
            
        # Get private attribute name for storing the resolved value
        private_name = f"_{self.name}"
        
        # Return cached value if exists
        if hasattr(instance, private_name) and getattr(instance, private_name) is not None:
            return getattr(instance, private_name)
            
        # Resolve dependency
        if isinstance(instance, DependencyBase):
            value = instance._ensure_dependency(
                self.name, 
                self.container_key, 
                self.fallback
            )
            
            # Cache resolved value
            if value is not None:
                setattr(instance, private_name, value)
                
            return value
            
        # Handle non-DependencyBase instances
        # ...
            
        return None  # No resolution possible
```

### 3. FlowBase

```python
class FlowBase(DependencyBase):
    """Base class for all flows with standardized dependency injection."""
    
    def __init__(self, container=None, **explicit_deps):
        """Initialize flow with container and explicit dependencies."""
        super().__init__(container)
        
        # Register explicitly provided dependencies
        for name, instance in explicit_deps.items():
            self._register_dependency(name, instance)
    
    def ensure_dependencies(self):
        """Ensure all required dependencies are available."""
        pass
        
    def cleanup(self):
        """Clean up resources when the flow is no longer needed."""
        pass
```

## Usage Pattern

### Declaring Dependencies

```python
class MyFlow(FlowBase):
    """A flow with simplified dependency handling."""
    
    # Define dependencies using descriptors
    database = Dependency()  # Uses "database" as container key
    logger = Dependency(container_key="logger_service")  # Custom container key
    config = Dependency(fallback=lambda: DefaultConfig())  # With fallback
```

### Explicit Dependency Injection (for testing)

```python
# Create flow with explicit dependencies
flow = MyFlow(
    database=mock_database,
    logger=mock_logger
)
```

### Container-based Injection

```python
# Create flow with container for dependency resolution
flow = MyFlow(container=container)
```

### Mixed Dependencies

```python
# Create flow with some explicit dependencies and others from container
flow = MyFlow(
    container=container,
    database=explicit_database  # Overrides container-provided database
)
```

## Benefits

1. **No Special Case Testing Logic** - Production code no longer detects test environment
2. **Cleaner Dependency Declaration** - Dependencies declared once at class level
3. **Lazy Loading** - Dependencies only resolved when needed
4. **Consistent Dependency Resolution** - Same pattern for all dependency types
5. **Better Testability** - Easy to inject explicit dependencies in tests
6. **Reduced Boilerplate** - Eliminates repeated initialization code

## Example Implementation

See `src/local_newsifier/flows/entity_tracking_flow_simplified.py` for a complete example of a flow using this pattern.

## Testing

To test classes using this pattern:

1. **Explicit Dependencies**:
   ```python
   flow = MyFlow(dependency1=mock1, dependency2=mock2)
   ```

2. **Mock Container**:
   ```python
   mock_container = Mock()
   mock_container.get.side_effect = lambda key: {...}.get(key)
   flow = MyFlow(container=mock_container)
   ```

3. **Verify Lazy Loading**:
   ```python
   # Track calls to container.get
   call_counts = {}
   def track_gets(key):
       call_counts[key] = call_counts.get(key, 0) + 1
       return mock_value
   
   mock_container.get.side_effect = track_gets
   
   # Access dependencies and verify load counts
   service1 = flow.service
   service2 = flow.service  # Should not increment count
   assert call_counts["service"] == 1  # Only loaded once
   ```

See `tests/flows/test_entity_tracking_flow_simplified.py` for complete examples of testing.
