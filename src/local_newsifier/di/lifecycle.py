"""
Lifecycle management for dependency-injected components.

This module provides utilities for managing the lifecycle of components
that need initialization and cleanup, such as services, tools, and flows.
It replaces the cleanup handler functionality from the DIContainer.
"""

import asyncio
import inspect
import logging
from contextlib import asynccontextmanager
from typing import Any, Callable, Dict, List, Optional

from fastapi import FastAPI

logger = logging.getLogger(__name__)

# Registry of cleanup handlers
_cleanup_handlers: Dict[str, Callable] = {}


def register_cleanup(component_name: str, handler: Callable[[Any], None]):
    """Register a cleanup handler for a component.
    
    Args:
        component_name: Name of the component
        handler: Cleanup function that takes the component instance
    """
    _cleanup_handlers[component_name] = handler
    logger.debug(f"Registered cleanup handler for {component_name}")


async def cleanup_resources():
    """Call all registered cleanup handlers."""
    if not _cleanup_handlers:
        logger.info("No cleanup handlers registered")
        return
        
    logger.info(f"Running {len(_cleanup_handlers)} cleanup handlers")
    
    for name, handler in _cleanup_handlers.items():
        try:
            logger.debug(f"Running cleanup handler for {name}")
            
            # Check if handler is a coroutine function
            if inspect.iscoroutinefunction(handler):
                await handler()
            else:
                handler()
                
            logger.debug(f"Completed cleanup for {name}")
        except Exception as e:
            logger.error(f"Error in cleanup handler for {name}: {e}")


def cleanup_handler(func):
    """Decorator to register a method as a cleanup handler.
    
    This decorator can be applied to methods that perform cleanup
    operations, and they will be automatically registered.
    
    Args:
        func: Method to register as cleanup handler
        
    Returns:
        The original function, unmodified
    """
    # Get the class and method name
    qualname = func.__qualname__
    class_name = qualname.split('.')[0]
    
    # Register the cleanup handler
    register_cleanup(class_name, func)
    
    return func


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Context manager for FastAPI lifespan event.
    
    This function provides lifespan management for FastAPI, handling
    startup and shutdown events to ensure proper resource initialization
    and cleanup.
    
    Args:
        app: FastAPI application
    """
    # Initialization code to run on startup
    from local_newsifier.di.init import init_injectable
    
    logger.info("Starting application lifecycle")
    await init_injectable(app)
    
    yield
    
    # Cleanup code to run on shutdown
    logger.info("Shutting down application")
    await cleanup_resources()
    

# Convenience synchronous version for testing
def run_cleanup():
    """Run all cleanup handlers synchronously.
    
    This is useful for testing or CLI applications where the asyncio
    event loop may not be readily available.
    """
    asyncio.run(cleanup_resources())