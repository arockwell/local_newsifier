"""Base class for components with dependency injection."""

from typing import Any, Dict, Optional, Callable, TypeVar, Union, cast

T = TypeVar('T')


class DependencyBase:
    """Base class for components with dependency injection.
    
    This class provides a standardized way to resolve dependencies from a container
    or fallback values, eliminating repetitive dependency resolution code in 
    service and flow classes.
    
    Attributes:
        container: Optional dependency injection container
        _dependencies: Dictionary of resolved dependencies
    """

    def __init__(self, container=None):
        """Initialize with optional container.
        
        Args:
            container: Optional dependency injection container
        """
        self.container = container
        self._dependencies: Dict[str, Any] = {}
        
    def _ensure_dependency(self, name: str, container_key: Optional[str] = None, 
                           fallback: Optional[Union[T, Callable[[], T]]] = None) -> Optional[T]:
        """Get or create a dependency.
        
        This method checks for a dependency in the following order:
        1. Return cached dependency if already resolved
        2. Try to get from container
        3. Use fallback value or function if provided
        
        Args:
            name: Attribute name to store the dependency
            container_key: Key to look up in container (defaults to name)
            fallback: Optional fallback value or factory function
            
        Returns:
            The resolved dependency, or None if it couldn't be resolved
        """
        # Return cached dependency if already resolved
        if name in self._dependencies:
            return cast(T, self._dependencies[name])
            
        # Use the provided name as container key if none specified
        container_key = container_key or name
        
        # Try to get from container
        value = None
        if self.container:
            value = self.container.get(container_key)
            
        # Use fallback if needed
        if value is None and fallback is not None:
            value = fallback() if callable(fallback) else fallback
            
        # Cache and return
        if value is not None:
            self._dependencies[name] = value
            
        return cast(T, value)

    def _register_dependency(self, name: str, value: Any) -> None:
        """Register a dependency directly.
        
        Args:
            name: Name to register the dependency under
            value: The dependency instance
        """
        self._dependencies[name] = value
