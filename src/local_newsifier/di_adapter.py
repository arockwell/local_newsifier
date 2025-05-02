"""Adapter layer to bridge between DIContainer and fastapi-injectable.

This module provides utilities to help during the transition from the custom
DIContainer to fastapi-injectable. It allows both systems to coexist and
interoperate during the migration process.
"""

from typing import Any, Dict, Optional, Type, TypeVar, cast

from local_newsifier.container import container as di_container

T = TypeVar("T")


class ContainerAdapter:
    """Adapter to bridge between DIContainer and fastapi-injectable.

    This class provides methods to get services from the DIContainer
    in a way that's compatible with fastapi-injectable patterns.
    """

    @staticmethod
    def get_service(service_type: Type[T], **kwargs) -> T:
        """Get a service from the DIContainer by type.

        This method attempts to find a service in the DIContainer
        based on the service type name, falling back to class name.

        Args:
            service_type: The type of service to retrieve
            **kwargs: Additional parameters to pass to get()

        Returns:
            The service instance

        Raises:
            ValueError: If the service cannot be found
        """
        # Try with module prefix (e.g., "entity_service")
        module_name = service_type.__module__.split(".")[-1]
        class_name = service_type.__name__
        
        # Format like "entity_service" from EntityService
        snake_case_name = "".join(
            ["_" + c.lower() if c.isupper() else c for c in class_name]
        ).lstrip("_")
        
        # Try different naming patterns
        service_names = [
            snake_case_name,  # entity_service
            f"{module_name}_{snake_case_name}",  # services_entity_service
            class_name.lower(),  # entityservice
        ]
        
        # Try to get the service from the container
        for name in service_names:
            service = di_container.get(name, **kwargs)
            if service is not None:
                return cast(T, service)
        
        # If not found by name, try to find by type
        for name, service in di_container._services.items():
            if isinstance(service, service_type):
                return cast(T, service)
                
        # Last resort: check factories and try to create the service
        for name, factory in di_container._factories.items():
            try:
                service = di_container._create_service(name, **kwargs)
                if isinstance(service, service_type):
                    return cast(T, service)
            except Exception:
                pass
                
        raise ValueError(f"Service of type {service_type.__name__} not found in container")


# Create an instance for easy importing
adapter = ContainerAdapter()