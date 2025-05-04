"""
Centralized initialization for fastapi-injectable.

This module provides a central point for initializing all fastapi-injectable providers,
registering lifecycle handlers, and configuring application-wide dependency injection.
It serves as a replacement for the DIContainer initialization in container.py.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List

from fastapi import FastAPI
from fastapi_injectable import register_app

logger = logging.getLogger(__name__)

# Store cleanup handlers for resource management
_cleanup_handlers = []


def register_cleanup_handler(handler):
    """Register a cleanup handler to be called during application shutdown.
    
    Args:
        handler: Callable that performs cleanup operations
    """
    _cleanup_handlers.append(handler)
    logger.debug(f"Registered cleanup handler: {handler.__name__}")


async def cleanup_resources():
    """Call all registered cleanup handlers."""
    logger.info(f"Running {len(_cleanup_handlers)} cleanup handlers")
    
    for handler in _cleanup_handlers:
        try:
            # Handle both async and sync cleanup handlers
            if asyncio.iscoroutinefunction(handler):
                await handler()
            else:
                handler()
        except Exception as e:
            logger.error(f"Error in cleanup handler {handler.__name__}: {e}")


def configure_providers(config: Optional[Dict[str, Any]] = None):
    """Configure fastapi-injectable providers with default parameters.
    
    This is the central location to set up default configurations for
    services, tools and other injectable components.
    
    Args:
        config: Optional configuration parameters
    """
    config = config or {}
    
    # Configure tool defaults
    configure_tool_defaults(config.get("tools", {}))
    
    # Configure service defaults
    configure_service_defaults(config.get("services", {}))
    
    # Configure flow defaults
    configure_flow_defaults(config.get("flows", {}))
    
    logger.info("Configured all injectable providers with defaults")


def configure_tool_defaults(tool_config: Dict[str, Any]):
    """Configure default parameters for tool providers.
    
    Args:
        tool_config: Tool-specific configuration parameters
    """
    # Configure output directories
    file_writer_dir = tool_config.get("file_writer_output_dir", "output")
    trend_reporter_dir = tool_config.get("trend_reporter_output_dir", "trend_output")
    
    # These configurations would be used by the providers when they're instantiated
    # The actual implementation would depend on how we implement configurable providers
    logger.info(f"Configured tool defaults - file_writer_dir: {file_writer_dir}, "
                f"trend_reporter_dir: {trend_reporter_dir}")


def configure_service_defaults(service_config: Dict[str, Any]):
    """Configure default parameters for service providers.
    
    Args:
        service_config: Service-specific configuration parameters
    """
    # Configure service settings
    logger.info("Configured service defaults")


def configure_flow_defaults(flow_config: Dict[str, Any]):
    """Configure default parameters for flow providers.
    
    Args:
        flow_config: Flow-specific configuration parameters
    """
    # Configure flow settings
    logger.info("Configured flow defaults")


def register_lifecycle_handlers():
    """Register lifecycle handlers for resource cleanup.
    
    This function registers cleanup handlers for services and tools
    that need proper resource management.
    """
    # Register cleanup for various components that need resource management
    from local_newsifier.services.article_service import ArticleService
    
    # Example handler registration - would be implemented in each component
    register_cleanup_handler(lambda: logger.info("Cleanup: ArticleService resources"))
    
    logger.info("Registered all lifecycle handlers")


async def init_injectable(app: Optional[FastAPI] = None, config: Optional[Dict[str, Any]] = None):
    """Initialize fastapi-injectable with central configuration.
    
    This function serves as the main entry point for configuring the
    fastapi-injectable system in the application.
    
    Args:
        app: Optional FastAPI application to register
        config: Optional configuration parameters
    """
    # Register the app if provided
    if app:
        await register_app(app)
        logger.info(f"Registered FastAPI app with fastapi-injectable: {app}")
    
    # Configure providers with defaults
    configure_providers(config)
    
    # Register lifecycle handlers
    register_lifecycle_handlers()
    
    logger.info("Initialized fastapi-injectable system")
    

# Convenience function for sync contexts
def init_injectable_sync(app: Optional[FastAPI] = None, config: Optional[Dict[str, Any]] = None):
    """Synchronous wrapper around init_injectable.
    
    Args:
        app: Optional FastAPI application to register
        config: Optional configuration parameters
    """
    asyncio.run(init_injectable(app, config))