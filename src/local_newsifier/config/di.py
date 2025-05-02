"""
Dependency Injection configuration for fastapi-injectable.

This module configures the fastapi-injectable system and provides
interfaces for gradual migration from the custom DI container.
"""

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional, Type, TypeVar

from fastapi import FastAPI
from fastapi_injectable import (
    Inject,
    Injectable,
    Scope,
    configure_logging,
    injectable,
    register_app,
    setup_graceful_shutdown,
)

from local_newsifier.di_container import DIContainer, Scope as DIContainerScope

# Initialize logging for fastapi-injectable
configure_logging(level=logging.INFO)

# Enable graceful shutdown to handle resource cleanup
setup_graceful_shutdown()

# Type variables for generic functions
T = TypeVar("T")
logger = logging.getLogger(__name__)


def scope_converter(scope: str) -> Scope:
    """Convert DIContainer scope to fastapi-injectable scope.
    
    Args:
        scope: DIContainer scope string
        
    Returns:
        Equivalent fastapi-injectable Scope enum value
    """
    scope_map = {
        DIContainerScope.SINGLETON.value: Scope.SINGLETON,
        DIContainerScope.TRANSIENT.value: Scope.TRANSIENT,
        DIContainerScope.SCOPED.value: Scope.REQUEST,  # Map scoped to request
    }
    return scope_map.get(scope.lower(), Scope.SINGLETON)


@asynccontextmanager
async def lifespan(app: FastAPI, di_container: DIContainer):
    """Lifespan context manager that registers fastapi-injectable.
    
    Use this when initializing FastAPI to ensure fastapi-injectable
    is properly set up and integrated with DIContainer.
    
    Args:
        app: FastAPI application
        di_container: The DIContainer instance to integrate with
    """
    # First register the app with fastapi-injectable
    logger.info("Initializing fastapi-injectable")
    await register_app(app)
    
    # Register existing DIContainer services with fastapi-injectable
    logger.info("Registering DIContainer services with fastapi-injectable")
    
    # Register direct service instances
    for name, service in di_container._services.items():
        if service is not None:
            try:
                logger.info(f"Registering service {name} with fastapi-injectable")
                
                # Create a provider function for this service
                @injectable(scope=scope_converter(di_container._scopes.get(name, "singleton")))
                def service_provider():
                    return di_container.get(name)
                
                # Set a meaningful name for the provider function
                service_provider.__name__ = f"get_{name}"
                
                # Keep track of the provider function within this module
                globals()[f"get_{name}"] = service_provider
                
            except Exception as e:
                logger.error(f"Error registering service {name}: {str(e)}")
    
    # Register factories
    for name, factory in di_container._factories.items():
        try:
            # Create a provider that calls the original factory with the container
            @injectable(scope=scope_converter(di_container._scopes.get(name, "singleton")))
            def factory_provider():
                return di_container.get(name)
            
            # Set meaningful name
            factory_provider.__name__ = f"get_{name}"
            
            # Store the provider function
            globals()[f"get_{name}"] = factory_provider
            
            logger.info(f"Registered factory {name} with fastapi-injectable")
        except Exception as e:
            logger.error(f"Error registering factory {name}: {str(e)}")
    
    # Let FastAPI handle requests
    yield
    
    # Cleanup when the app shuts down
    logger.info("Cleaning up fastapi-injectable")


def register_provider(name: str, provider_func: Any, scope: Scope = Scope.SINGLETON):
    """Register a provider function with fastapi-injectable.
    
    This is a utility function for registering new provider functions
    that are not tied to the existing DIContainer.
    
    Args:
        name: The provider function name
        provider_func: The injectable provider function
        scope: The scope for the provider (default: Scope.SINGLETON)
    """
    # Decorate the function if not already decorated
    if not hasattr(provider_func, "__injected__"):
        provider_func = injectable(scope=scope)(provider_func)
    
    # Store the provider function in this module's globals
    globals()[name] = provider_func
    
    logger.info(f"Registered provider function {name}")
    
    return provider_func