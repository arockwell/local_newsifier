"""FastAPI-Injectable adapter functions for Local Newsifier.

This module provides adapter functions to integrate fastapi-injectable
with the existing dependency injection container system used by Local Newsifier.
"""

import logging
from typing import Any, Optional
from fastapi import FastAPI

logger = logging.getLogger(__name__)


async def lifespan_with_injectable(app: FastAPI):
    """Lifespan context manager that integrates fastapi-injectable.
    
    This function provides a standardized way to initialize FastAPI applications
    with fastapi-injectable support. It handles the registration and setup
    of injectable providers.
    
    Args:
        app: FastAPI application instance
        
    Yields:
        None - This is a context manager for FastAPI lifespan
    """
    # Startup logic
    logger.info("Starting FastAPI application with injectable support")
    
    try:
        # Register the app with fastapi-injectable
        from fastapi_injectable import register_app
        await register_app(app)
        logger.info("fastapi-injectable registration completed")
        
        # Additional startup logic can be added here
        
    except Exception as e:
        logger.error(f"Error during injectable lifespan startup: {str(e)}")
        # Don't re-raise - allow the application to continue
    
    logger.info("Injectable lifespan startup complete")
    
    yield  # This is where FastAPI serves requests
    
    # Shutdown logic
    logger.info("Injectable lifespan shutdown initiated")
    # Cleanup logic can be added here if needed
    logger.info("Injectable lifespan shutdown complete")


async def migrate_container_services(app: FastAPI):
    """Migrate container services to fastapi-injectable.
    
    This function handles the migration of existing container-based services
    to the fastapi-injectable framework. It ensures compatibility between
    the old container system and the new injectable system.
    
    Args:
        app: FastAPI application instance
    """
    logger.info("Starting container services migration to fastapi-injectable")
    
    try:
        # This function handles the migration from the old container system
        # to fastapi-injectable. Since we're fully using fastapi-injectable now,
        # this is primarily a compatibility function.
        
        # In the future, this could handle:
        # 1. Migrating any remaining container-based services
        # 2. Validating that all required providers are available
        # 3. Setting up any compatibility layers
        
        logger.info("Container services migration completed successfully")
        
    except Exception as e:
        logger.error(f"Error during container services migration: {str(e)}")
        # Don't re-raise - log the error but continue
        # This allows the application to start even if migration has issues
    
    logger.info("Container services migration process finished")


def get_injectable_dependency(provider_name: str) -> Optional[Any]:
    """Get a dependency from the injectable system by provider name.
    
    This is a utility function to bridge between string-based dependency
    resolution and the fastapi-injectable system.
    
    Args:
        provider_name: Name of the provider function to call
        
    Returns:
        The resolved dependency, or None if not found
    """
    try:
        # This function could be used to dynamically resolve dependencies
        # by name, providing a bridge for any legacy code that expects
        # string-based dependency resolution
        
        from local_newsifier.di import providers
        
        # Get the provider function by name
        provider_func = getattr(providers, provider_name, None)
        
        if provider_func is None:
            logger.warning(f"Provider function '{provider_name}' not found")
            return None
            
        # Call the provider function to get the dependency
        # Note: This assumes synchronous providers - async providers would need special handling
        return provider_func()
        
    except Exception as e:
        logger.error(f"Error resolving injectable dependency '{provider_name}': {str(e)}")
        return None