"""Adapter module for integrating fastapi-injectable with existing DIContainer.

This module provides integration between the current DIContainer and
fastapi-injectable. It allows services to be registered with both systems
and provides smooth transition from one to the other.
"""

import inspect
import logging
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, get_type_hints

from fastapi import Depends, FastAPI
from fastapi_injectable import injectable, get_injected_obj, register_app
from contextlib import asynccontextmanager

from local_newsifier.container import container as di_container

T = TypeVar("T")
logger = logging.getLogger(__name__)


def get_service_factory(service_name: str) -> Callable:
    """Create a factory function that gets a service from DIContainer.
    
    Args:
        service_name: Name of the service in DIContainer
        
    Returns:
        Factory function that returns the service
    """
    @injectable(use_cache=True)
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


def register_container_service(service_name: str) -> Callable:
    """Register a single DIContainer service with fastapi-injectable.
    
    Args:
        service_name: Name of the service in DIContainer
        
    Returns:
        Factory function for the service
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