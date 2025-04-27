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

        Args:
            name: The service name/key

        Returns:
            The service instance, or None if not found
        """
        # If service doesn't exist but has a factory, create it
        if name not in self._services and name in self._factories:
            self._services[name] = self._factories[name](self)
        
        # Return the service or None if not found
        return self._services.get(name)
