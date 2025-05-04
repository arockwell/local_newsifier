"""
Dependency Injection Container

This module provides a simple dependency injection container to resolve
circular dependencies and improve testability. It enables service registration,
factory method registration, and lazy loading of services.
"""

from enum import Enum
from typing import Any, Dict, Callable, Optional, Set, TypeVar, Generic


class Scope(str, Enum):
    """Scope enum for service lifetime management."""
    SINGLETON = "singleton"  # One instance for the entire application
    TRANSIENT = "transient"  # New instance every time it's requested
    SCOPED = "scoped"        # One instance per scope (e.g., per request)


T = TypeVar('T')


class DIContainer:
    """A simple dependency injection container.

    This container allows registering service instances and factory functions
    for creating services on demand. It handles lazy loading of services,
    resolves circular dependencies, and manages service lifetimes.
    """

    def __init__(self):
        """Initialize an empty container."""
        self._services = {}         # Registered service instances
        self._factories = {}        # Factory functions for lazy loading services
        self._scopes = {}           # Lifetime scope of each service
        self._creating = set()      # Set of services currently being created (for circular dep detection)
        self._cleanup_handlers = {} # Handlers for cleanup when a service is removed
        
    def get_all_services(self) -> Dict[str, Any]:
        """Get all registered service instances.
        
        Returns:
            A copy of the dictionary mapping service names to their instances
        """
        return self._services.copy()
        
    def get_all_factories(self) -> Dict[str, Callable]:
        """Get all registered factory functions.
        
        Returns:
            A copy of the dictionary mapping service names to their factory functions
        """
        return self._factories.copy()

    def register(self, name: str, instance: Any, scope: Scope = Scope.SINGLETON) -> 'DIContainer':
        """Register a service instance directly.

        Args:
            name: The service name/key
            instance: The service instance
            scope: The service lifetime scope (defaults to singleton)

        Returns:
            The container instance for method chaining
        """
        self._services[name] = instance
        self._scopes[name] = scope
        return self

    def register_factory(self, name: str, 
                         factory: Callable[['DIContainer'], Any], 
                         scope: Scope = Scope.SINGLETON) -> 'DIContainer':
        """Register a factory function that creates the service when needed.

        Args:
            name: The service name/key
            factory: Function that creates the service, takes container as argument
            scope: The service lifetime scope (defaults to singleton)

        Returns:
            The container instance for method chaining
        """
        self._factories[name] = factory
        self._scopes[name] = scope
        return self

    def register_factory_with_params(self, name: str, 
                                    factory: Callable[..., Any], 
                                    scope: Scope = Scope.SINGLETON) -> 'DIContainer':
        """Register a factory function that can accept additional parameters.

        This allows registering factories that can take parameters beyond just the container.
        When resolved, if no parameters are provided, it will call the factory with just the container.

        Args:
            name: The service name/key
            factory: Function that creates the service with parameters
            scope: The service lifetime scope (defaults to singleton)

        Returns:
            The container instance for method chaining
        """
        # Mark this factory as one that accepts parameters
        self._factories[name] = factory
        self._scopes[name] = scope
        # Store a flag indicating this is a parameterized factory
        setattr(self._factories[name], '_accepts_params', True)
        return self

    def register_cleanup(self, name: str, handler: Callable[[Any], None]) -> 'DIContainer':
        """Register a cleanup handler for a service.

        The handler will be called when the service is removed from the container,
        allowing proper resource cleanup (connections, file handles, etc.)

        Args:
            name: The service name/key
            handler: Function that cleans up the service, takes service instance as argument

        Returns:
            The container instance for method chaining
        """
        self._cleanup_handlers[name] = handler
        return self

    def get(self, name: str, **kwargs) -> Any:
        """Get a service by name, creating it via factory if needed.

        This method handles circular dependencies by detecting when a service
        is already in the process of being created, and returning a partially
        initialized service in that case.

        Args:
            name: The service name/key
            **kwargs: Optional parameters to pass to the factory function

        Returns:
            The service instance, or None if not found
        """
        # Check if we have parameters and a parameterized factory
        has_params = bool(kwargs)
        is_parameterized = name in self._factories and hasattr(self._factories[name], '_accepts_params') and self._factories[name]._accepts_params
        
        # For parameterized factories with parameters, always create a new transient instance
        if has_params and is_parameterized and name in self._factories:
            return self._create_service(name, store_instance=False, **kwargs)
        
        # For transient services, always create a new instance (but follow scope rules)
        if name in self._scopes and self._scopes[name] == Scope.TRANSIENT and name in self._factories:
            return self._create_service(name, **kwargs)
            
        # Return the service if it already exists
        if name in self._services:
            return self._services[name]
            
        # If no factory exists for this service, return None
        if name not in self._factories:
            return None
            
        # Create the service (and store according to scope)
        return self._create_service(name, **kwargs)

    def _create_service(self, name: str, store_instance: bool = True, **kwargs) -> Any:
        """Internal method to create a service from its factory.
        
        Handles circular dependencies and respects service scope.
        
        Args:
            name: The service name/key
            store_instance: Whether to store the instance in the container
            **kwargs: Optional parameters to pass to the factory
            
        Returns:
            The service instance
        """
        # If we're already creating this service (circular dependency),
        # create a placeholder to break the cycle
        if name in self._creating and store_instance:
            # For dict-like services, create a placeholder if it doesn't already exist
            if name not in self._services:
                self._services[name] = {}
            return self._services[name]
            
        # Mark that we're creating this service to detect circular dependencies
        self._creating.add(name)
        
        try:
            # Only create placeholders for singleton or scoped services that we'll store
            if store_instance and self._scopes[name] != Scope.TRANSIENT:
                # Create a placeholder if one doesn't already exist
                if name not in self._services:
                    self._services[name] = {}
                    
            # Create the service using its factory and get the result
            factory = self._factories[name]
            
            # Check if this is a factory that accepts parameters
            accepts_params = hasattr(factory, '_accepts_params') and factory._accepts_params
            
            if kwargs and accepts_params:
                # Pass kwargs for parameterized factories
                result = factory(self, **kwargs)
            elif kwargs and not accepts_params:
                # Regular factories ignore kwargs
                result = factory(self)
            else:
                # No kwargs or factory doesn't accept them
                result = factory(self)
            
            # Only store the result for singleton or scoped services
            if store_instance and self._scopes[name] != Scope.TRANSIENT:
                # If the result is a dict, update the placeholder with the result's contents
                # This ensures existing references to the placeholder get the updated values
                if isinstance(result, dict) and isinstance(self._services[name], dict):
                    self._services[name].update(result)
                    return self._services[name]
                else:
                    # Otherwise replace the placeholder completely
                    self._services[name] = result
            
            return result
        finally:
            # Remove from creating set regardless of success/failure
            self._creating.remove(name)

    def remove(self, name: str) -> bool:
        """Remove a service from the container.
        
        If a cleanup handler is registered for the service, it will be called.
        
        Args:
            name: The service name/key
            
        Returns:
            True if the service was removed, False if it didn't exist
        """
        if name not in self._services:
            return False
            
        # Call cleanup handler if one exists
        if name in self._cleanup_handlers and self._services[name] is not None:
            try:
                self._cleanup_handlers[name](self._services[name])
            except Exception:
                # Log error but continue with removal
                pass
                
        # Remove service
        del self._services[name]
        
        # Remove metadata
        if name in self._scopes:
            del self._scopes[name]
        if name in self._cleanup_handlers:
            del self._cleanup_handlers[name]
        if name in self._factories:
            del self._factories[name]
            
        return True

    def clear(self) -> None:
        """Remove all services from the container.
        
        Calls cleanup handlers for all services that have them.
        """
        # Create a copy of service names to avoid modifying during iteration
        service_names = list(self._services.keys())
        
        # Remove each service
        for name in service_names:
            self.remove(name)
            
        # Ensure all collections are empty
        self._services.clear()
        self._factories.clear()
        self._scopes.clear()
        self._cleanup_handlers.clear()
        self._creating.clear()

    def has(self, name: str) -> bool:
        """Check if a service is registered or can be created.
        
        Args:
            name: The service name/key
            
        Returns:
            True if the service exists or can be created, False otherwise
        """
        return name in self._services or name in self._factories

    def create_child_scope(self) -> 'DIContainer':
        """Create a new child container that inherits from this container.
        
        The child container will have access to all singleton services from the parent,
        but will have its own instances of scoped services.
        
        Returns:
            A new DIContainer instance
        """
        child = DIContainer()
        
        # Copy all factories to the child
        for name, factory in self._factories.items():
            child._factories[name] = factory
            child._scopes[name] = self._scopes.get(name, Scope.SINGLETON)
            
        # Copy singleton services to the child
        for name, service in self._services.items():
            if self._scopes.get(name) == Scope.SINGLETON:
                child._services[name] = service
                
        # Copy cleanup handlers
        for name, handler in self._cleanup_handlers.items():
            child._cleanup_handlers[name] = handler
            
        return child
