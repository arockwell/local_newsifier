"""
Dependency Injection Container

This module provides a simple dependency injection container to resolve
circular dependencies and improve testability. It enables service registration,
factory method registration, and lazy loading of services.
"""

from enum import Enum
import warnings
from typing import Any, Dict, Callable, Iterator, List, Optional, Set, Tuple, TypeVar, Generic


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
        self.__services = {}         # Registered service instances
        self.__factories = {}        # Factory functions for lazy loading services
        self.__scopes = {}           # Lifetime scope of each service
        self.__creating = set()      # Set of services currently being created (for circular dep detection)
        self.__cleanup_handlers = {} # Handlers for cleanup when a service is removed

    def register(self, name: str, instance: Any, scope: Scope = Scope.SINGLETON) -> 'DIContainer':
        """Register a service instance directly.

        Args:
            name: The service name/key
            instance: The service instance
            scope: The service lifetime scope (defaults to singleton)

        Returns:
            The container instance for method chaining
        """
        self.__services[name] = instance
        self.__scopes[name] = scope
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
        self.__factories[name] = factory
        self.__scopes[name] = scope
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
        self.__factories[name] = factory
        self.__scopes[name] = scope
        # Store a flag indicating this is a parameterized factory
        setattr(self.__factories[name], '_accepts_params', True)
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
        self.__cleanup_handlers[name] = handler
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
        is_parameterized = name in self.__factories and hasattr(self.__factories[name], '_accepts_params') and self.__factories[name]._accepts_params
        
        # For parameterized factories with parameters, always create a new transient instance
        if has_params and is_parameterized and name in self.__factories:
            return self.__create_service(name, store_instance=False, **kwargs)
        
        # For transient services, always create a new instance (but follow scope rules)
        if name in self.__scopes and self.__scopes[name] == Scope.TRANSIENT and name in self.__factories:
            return self.__create_service(name, **kwargs)
            
        # Return the service if it already exists
        if name in self.__services:
            return self.__services[name]
            
        # If no factory exists for this service, return None
        if name not in self.__factories:
            return None
            
        # Create the service (and store according to scope)
        return self.__create_service(name, **kwargs)

    def __create_service(self, name: str, store_instance: bool = True, **kwargs) -> Any:
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
        if name in self.__creating and store_instance:
            # For dict-like services, create a placeholder if it doesn't already exist
            if name not in self.__services:
                self.__services[name] = {}
            return self.__services[name]
            
        # Mark that we're creating this service to detect circular dependencies
        self.__creating.add(name)
        
        try:
            # Only create placeholders for singleton or scoped services that we'll store
            if store_instance and self.__scopes[name] != Scope.TRANSIENT:
                # Create a placeholder if one doesn't already exist
                if name not in self.__services:
                    self.__services[name] = {}
                    
            # Create the service using its factory and get the result
            factory = self.__factories[name]
            
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
            if store_instance and self.__scopes[name] != Scope.TRANSIENT:
                # If the result is a dict, update the placeholder with the result's contents
                # This ensures existing references to the placeholder get the updated values
                if isinstance(result, dict) and isinstance(self.__services[name], dict):
                    self.__services[name].update(result)
                    return self.__services[name]
                else:
                    # Otherwise replace the placeholder completely
                    self.__services[name] = result
            
            return result
        finally:
            # Remove from creating set regardless of success/failure
            self.__creating.remove(name)

    def remove(self, name: str) -> bool:
        """Remove a service from the container.
        
        If a cleanup handler is registered for the service, it will be called.
        
        Args:
            name: The service name/key
            
        Returns:
            True if the service was removed, False if it didn't exist
        """
        if name not in self.__services:
            return False
            
        # Call cleanup handler if one exists
        if name in self.__cleanup_handlers and self.__services[name] is not None:
            try:
                self.__cleanup_handlers[name](self.__services[name])
            except Exception:
                # Log error but continue with removal
                pass
                
        # Remove service
        del self.__services[name]
        
        # Remove metadata
        if name in self.__scopes:
            del self.__scopes[name]
        if name in self.__cleanup_handlers:
            del self.__cleanup_handlers[name]
        if name in self.__factories:
            del self.__factories[name]
            
        return True

    def clear(self) -> None:
        """Remove all services from the container.
        
        Calls cleanup handlers for all services that have them.
        """
        # Create a copy of service names to avoid modifying during iteration
        service_names = list(self.__services.keys())
        
        # Remove each service
        for name in service_names:
            self.remove(name)
            
        # Ensure all collections are empty
        self.__services.clear()
        self.__factories.clear()
        self.__scopes.clear()
        self.__cleanup_handlers.clear()
        self.__creating.clear()

    def has(self, name: str) -> bool:
        """Check if a service is registered or can be created.
        
        Args:
            name: The service name/key
            
        Returns:
            True if the service exists or can be created, False otherwise
        """
        return name in self.__services or name in self.__factories

    def create_child_scope(self) -> 'DIContainer':
        """Create a new child container that inherits from this container.
        
        The child container will have access to all singleton services from the parent,
        but will have its own instances of scoped services.
        
        Returns:
            A new DIContainer instance
        """
        child = DIContainer()
        
        # Copy all factories to the child
        for name, factory in self.__factories.items():
            child._DIContainer__factories[name] = factory
            child._DIContainer__scopes[name] = self.__scopes.get(name, Scope.SINGLETON)
            
        # Copy singleton services to the child
        for name, service in self.__services.items():
            if self.__scopes.get(name) == Scope.SINGLETON:
                child._DIContainer__services[name] = service
                
        # Copy cleanup handlers
        for name, handler in self.__cleanup_handlers.items():
            child._DIContainer__cleanup_handlers[name] = handler
            
        return child
        
    # Public API methods
    
    def get_all_services(self) -> Dict[str, Any]:
        """Get all registered service instances.
        
        This method provides a read-only view of all registered service instances.
        
        Returns:
            Dictionary mapping service names to their instances
        """
        return self.__services.copy()
        
    def get_all_factories(self) -> Dict[str, Callable]:
        """Get all registered factory functions.
        
        This method provides a read-only view of all registered factory functions.
        
        Returns:
            Dictionary mapping service names to their factory functions
        """
        return self.__factories.copy()
        
    def get_service_scope(self, name: str) -> Optional[Scope]:
        """Get the scope of a service.
        
        Args:
            name: The service name/key
            
        Returns:
            The service scope, or None if the service is not registered
        """
        return self.__scopes.get(name)
        
    def create_service(self, name: str, **kwargs) -> Any:
        """Create a service instance using its registered factory.
        
        This method is useful for creating a new instance of a service
        regardless of its scope. It does not store the instance in the container.
        
        Args:
            name: The service name/key
            **kwargs: Optional parameters to pass to the factory
            
        Returns:
            The service instance, or None if not found
            
        Raises:
            KeyError: If the service is not registered with a factory
        """
        if name not in self.__factories:
            raise KeyError(f"No factory registered for service '{name}'")
            
        return self.__create_service(name, store_instance=False, **kwargs)
        
    def get_service_names(self) -> List[str]:
        """Get the names of all registered services.
        
        This method returns a list of all service names in the container,
        including both instances and factories.
        
        Returns:
            List of service names
        """
        # Combine services and factories, removing duplicates
        return list(set(list(self.__services.keys()) + list(self.__factories.keys())))
        
    def get_services_by_pattern(self, pattern: str) -> List[str]:
        """Get service names that match a pattern.
        
        This method returns a list of service names that contain the given pattern.
        
        Args:
            pattern: The pattern to match against service names
            
        Returns:
            List of matching service names
        """
        return [name for name in self.get_service_names() if pattern in name]
        
    def get_services_by_scope(self, scope: Scope) -> List[str]:
        """Get service names with a specific scope.
        
        This method returns a list of service names that have the given scope.
        
        Args:
            scope: The scope to filter by
            
        Returns:
            List of matching service names
        """
        return [name for name, scp in self.__scopes.items() if scp == scope]
        
    # Property accessors with deprecation warnings
    
    @property
    def _services(self) -> Dict[str, Any]:
        """Property accessor for _services with deprecation warning.
        
        This property provides backward compatibility for code that
        directly accesses the _services attribute. It emits a deprecation
        warning and should be replaced with get_all_services().
        
        Returns:
            Dictionary mapping service names to their instances
        """
        warnings.warn(
            "Direct access to DIContainer._services is deprecated. "
            "Use get_all_services() instead.",
            DeprecationWarning, 
            stacklevel=2
        )
        return self.__services
        
    @property
    def _factories(self) -> Dict[str, Callable]:
        """Property accessor for _factories with deprecation warning.
        
        This property provides backward compatibility for code that
        directly accesses the _factories attribute. It emits a deprecation
        warning and should be replaced with get_all_factories().
        
        Returns:
            Dictionary mapping service names to their factory functions
        """
        warnings.warn(
            "Direct access to DIContainer._factories is deprecated. "
            "Use get_all_factories() instead.",
            DeprecationWarning, 
            stacklevel=2
        )
        return self.__factories
        
    @property
    def _scopes(self) -> Dict[str, Scope]:
        """Property accessor for _scopes with deprecation warning.
        
        This property provides backward compatibility for code that
        directly accesses the _scopes attribute. It emits a deprecation
        warning and should be replaced with get_service_scope().
        
        Returns:
            Dictionary mapping service names to their scopes
        """
        warnings.warn(
            "Direct access to DIContainer._scopes is deprecated. "
            "Use get_service_scope() instead.",
            DeprecationWarning, 
            stacklevel=2
        )
        return self.__scopes
        
    @property
    def _creating(self) -> Set[str]:
        """Property accessor for _creating with deprecation warning.
        
        This property provides backward compatibility for code that
        directly accesses the _creating attribute. It emits a deprecation
        warning as this is an internal implementation detail.
        
        Returns:
            Set of service names currently being created
        """
        warnings.warn(
            "Direct access to DIContainer._creating is deprecated. "
            "This is an internal implementation detail.",
            DeprecationWarning, 
            stacklevel=2
        )
        return self.__creating
        
    @property
    def _cleanup_handlers(self) -> Dict[str, Callable]:
        """Property accessor for _cleanup_handlers with deprecation warning.
        
        This property provides backward compatibility for code that
        directly accesses the _cleanup_handlers attribute. It emits a deprecation
        warning as this is an internal implementation detail.
        
        Returns:
            Dictionary mapping service names to their cleanup handlers
        """
        warnings.warn(
            "Direct access to DIContainer._cleanup_handlers is deprecated. "
            "This is an internal implementation detail.",
            DeprecationWarning, 
            stacklevel=2
        )
        return self.__cleanup_handlers
