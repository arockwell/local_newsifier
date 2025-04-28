"""
Dependency Injection Container

This module provides a simple dependency injection container to resolve
circular dependencies and improve testability. It enables service registration,
factory method registration, and lazy loading of services.
"""

from typing import Any, Dict, Callable


class DIContainer:
    """A simple dependency injection container.

    This container allows registering service instances and factory functions
    for creating services on demand. It handles lazy loading of services
    and resolves circular dependencies.
    """

    def __init__(self):
        """Initialize an empty container."""
        self._services = {}  # Registered service instances
        self._factories = {}  # Factory functions for lazy loading services
        self._creating = set()  # Set of services currently being created (for circular dep detection)

    def register(self, name: str, instance: Any) -> 'DIContainer':
        """Register a service instance directly.

        Args:
            name: The service name/key
            instance: The service instance

        Returns:
            The container instance for method chaining
        """
        self._services[name] = instance
        return self

    def register_factory(self, name: str, factory: Callable[['DIContainer'], Any]) -> 'DIContainer':
        """Register a factory function that creates the service when needed.

        Args:
            name: The service name/key
            factory: Function that creates the service, takes container as argument

        Returns:
            The container instance for method chaining
        """
        self._factories[name] = factory
        return self

    def get(self, name: str) -> Any:
        """Get a service by name, creating it via factory if needed.

        This method handles circular dependencies by detecting when a service
        is already in the process of being created, and returning a partially
        initialized service in that case.

        Args:
            name: The service name/key

        Returns:
            The service instance, or None if not found
        """
        # Return the service if it already exists
        if name in self._services:
            return self._services[name]
            
        # If no factory exists for this service, return None
        if name not in self._factories:
            return None
            
        # If we're already creating this service (circular dependency),
        # create a placeholder to break the cycle
        if name in self._creating:
            # For dict-like services, create a placeholder if it doesn't already exist
            if name not in self._services:
                self._services[name] = {}
            return self._services[name]
            
        # Mark that we're creating this service to detect circular dependencies
        self._creating.add(name)
        
        try:
            # Create a placeholder if one doesn't already exist
            if name not in self._services:
                self._services[name] = {}
                
            # Create the service using its factory and get the result
            result = self._factories[name](self)
            
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
