"""Adapter module for integrating fastapi-injectable with the DIContainer.

This module provides a comprehensive adapter layer between the current DIContainer
and fastapi-injectable, allowing both systems to coexist during migration. It includes
utilities for registering services, resolving dependencies, and providing compatibility
between the two DI systems.
"""

import inspect
import logging
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union, cast, get_type_hints

from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from fastapi_injectable import injectable, get_injected_obj, register_app, Scope

from local_newsifier.container import container as di_container

T = TypeVar("T")
logger = logging.getLogger(__name__)


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


def scope_converter(scope: str) -> Scope:
    """Convert DIContainer scope to fastapi-injectable scope.
    
    Args:
        scope: DIContainer scope string ("singleton", "transient", "scoped")
        
    Returns:
        Equivalent fastapi-injectable Scope enum value
    """
    scope_map = {
        "singleton": Scope.SINGLETON,
        "transient": Scope.TRANSIENT,
        "scoped": Scope.REQUEST  # Map scoped to request in fastapi-injectable
    }
    return scope_map.get(scope.lower(), Scope.SINGLETON)


def get_service_factory(service_name: str) -> Callable:
    """Create a factory function that gets a service from DIContainer.
    
    Args:
        service_name: Name of the service in DIContainer
        
    Returns:
        Factory function that returns the service
    """
    # Get the scope from DIContainer
    di_scope = di_container._scopes.get(service_name, "singleton")
    injectable_scope = scope_converter(di_scope)
    
    @injectable(scope=injectable_scope, use_cache=True)
    def service_factory():
        """Factory function to get service from DIContainer."""
        return di_container.get(service_name)
    
    # Set better function name for debugging
    service_factory.__name__ = f"get_{service_name}"
    
    return service_factory


def register_with_injectable(service_name: str, service_class: Type[T]) -> Callable:
    """Register a service from DIContainer with fastapi-injectable.
    
    This function takes a service that is already registered with DIContainer
    and makes it available through fastapi-injectable as well.
    
    Args:
        service_name: Name of the service in DIContainer
        service_class: Class type of the service
        
    Returns:
        Factory function that will return the service when called
    """
    factory = get_service_factory(service_name)
    
    # Return the factory for use by other code
    return factory


def inject_adapter(func: Callable) -> Callable:
    """Decorator to adapt between fastapi-injectable and DIContainer.
    
    This decorator allows FastAPI endpoints to use dependencies that may
    come from either system.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        # For async functions
        # Inject dependencies using fastapi-injectable
        result = await get_injected_obj(func, args=list(args), kwargs=kwargs.copy())
        return result
        
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        # For sync functions
        # Inject dependencies using fastapi-injectable
        result = get_injected_obj(func, args=list(args), kwargs=kwargs.copy())
        return result
    
    # Choose the right wrapper based on whether the function is async
    if inspect.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def register_container_service(service_name: str) -> Union[Callable, None]:
    """Register a single DIContainer service with fastapi-injectable.
    
    Args:
        service_name: Name of the service in DIContainer
        
    Returns:
        Factory function for the service, or None if registration failed
    """
    try:
        service = di_container.get(service_name)
        if service is not None:
            service_class = service.__class__
            factory = register_with_injectable(service_name, service_class)
            logger.info(f"Registered service {service_name} with fastapi-injectable")
            return factory
        else:
            logger.warning(f"Service {service_name} not found in DIContainer")
            return None
    except (AttributeError, TypeError) as e:
        logger.error(f"Type error registering {service_name}: {str(e)}")
        return None
    except ValueError as e:
        logger.error(f"Value error registering {service_name}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error registering {service_name}: {str(e)}")
        return None


def register_bulk_services(service_names: List[str]) -> Dict[str, Callable]:
    """Register multiple services with fastapi-injectable.
    
    Args:
        service_names: List of service names in DIContainer
        
    Returns:
        Dictionary mapping service names to their factory functions
    """
    factories = {}
    for service_name in service_names:
        factory = register_container_service(service_name)
        if factory:
            factories[service_name] = factory
    
    return factories


def get_service_by_type(service_type: Type[T], **kwargs) -> T:
    """Get a service from DIContainer by type.
    
    This is a convenience function that delegates to ContainerAdapter.get_service.
    
    Args:
        service_type: Type of service to retrieve
        **kwargs: Additional parameters to pass to the container
        
    Returns:
        Service instance
        
    Raises:
        ValueError: If service not found
    """
    return adapter.get_service(service_type, **kwargs)


async def migrate_container_services(app: FastAPI) -> None:
    """Register all DIContainer services with fastapi-injectable.
    
    This function goes through all services in DIContainer and
    registers them with fastapi-injectable for compatibility.
    
    Args:
        app: FastAPI application to register with fastapi-injectable
    """
    # Register the FastAPI app with fastapi-injectable
    await register_app(app)
    
    # Register direct service instances
    for name, service in di_container._services.items():
        if service is not None:
            try:
                service_class = service.__class__
                register_with_injectable(name, service_class)
                logger.info(f"Registered service {name} with fastapi-injectable")
            except (AttributeError, TypeError) as e:
                logger.error(f"Type error registering service {name}: {str(e)}")
            except ValueError as e:
                logger.error(f"Value error registering service {name}: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error registering service {name}: {str(e)}")
    
    # Register factory-created services
    registered_factories = 0
    for name, factory in di_container._factories.items():
        # Try to determine the return type from factory signature
        try:
            # Try to get a service instance to determine type
            service = di_container.get(name)
            if service is not None:
                service_class = service.__class__
                register_with_injectable(name, service_class)
                registered_factories += 1
                logger.info(f"Registered factory service {name} with fastapi-injectable")
        except (AttributeError, TypeError) as e:
            logger.warning(f"Type error registering factory {name}: {str(e)}")
        except ValueError as e:
            logger.warning(f"Value error registering factory {name}: {str(e)}")
        except Exception as e:
            logger.warning(f"Could not register factory {name}: {str(e)}")
    
    logger.info(f"Migration complete. Registered {len(di_container._services)} services and {registered_factories} factories.")
    
    
@asynccontextmanager
async def lifespan_with_injectable(app: FastAPI):
    """Lifespan context manager that sets up fastapi-injectable.
    
    Use this when initializing your FastAPI app to ensure
    fastapi-injectable is properly set up.
    
    Args:
        app: FastAPI application
    """
    # Initialize fastapi-injectable
    logger.info("Initializing fastapi-injectable")
    await register_app(app)
    
    # Register DIContainer services
    logger.info("Registering DIContainer services with fastapi-injectable")
    await migrate_container_services(app)
    
    # Let FastAPI handle requests
    yield
    
    # Cleanup when the app shuts down
    logger.info("Cleaning up fastapi-injectable")