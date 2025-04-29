"""Descriptors for simplified dependency injection."""

from typing import Any, Callable, Optional, TypeVar, cast

T = TypeVar('T')

class Dependency:
    """Descriptor for lazy dependency resolution.
    
    This descriptor allows for cleaner dependency declaration at the class level.
    Dependencies are only resolved when accessed, and the resolved values are cached.
    
    Example:
        ```python
        class MyService(DependencyBase):
            # Define dependencies using descriptors
            database = Dependency()
            logger = Dependency(container_key="logger_service")
            config = Dependency(fallback=lambda: DefaultConfig())
        ```
    """
    
    def __init__(self, container_key: Optional[str] = None, fallback: Any = None):
        """Initialize the dependency descriptor.
        
        Args:
            container_key: Key to look up in container (defaults to attribute name)
            fallback: Default value or factory to use if not in container
        """
        self.name: str = ""  # Will be set by __set_name__
        self.container_key = container_key
        self.fallback = fallback
        
    def __set_name__(self, owner, name):
        """Set descriptor name when class is defined."""
        self.name = name
        if not self.container_key:
            # Convert attribute name to container key following project conventions
            # E.g., "entity_extractor" -> "entity_extractor_tool"
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
            
        # Resolve dependency if we have a DependencyBase instance
        from local_newsifier.di.dependency_base import DependencyBase
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
            
        # Direct container access if not using DependencyBase but has container
        if hasattr(instance, "container") and instance.container:
            value = instance.container.get(self.container_key)
            if value is None and self.fallback is not None:
                value = self.fallback() if callable(self.fallback) else self.fallback
                
            # Cache resolved value
            if value is not None:
                setattr(instance, private_name, value)
                
            return value
            
        # Fallback if available
        if self.fallback is not None:
            value = self.fallback() if callable(self.fallback) else self.fallback
            
            # Cache resolved value
            if value is not None:
                setattr(instance, private_name, value)
                
            return value
            
        return None  # No resolution possible
