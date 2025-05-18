"""
Local Newsifier CLI - Main Entry Point with Enhanced Event Loop Handling

The `nf` command is the entry point for the Local Newsifier CLI.
This module provides a foundation for managing RSS feeds and other local newsifier
operations from the command line, with robust event loop handling to prevent
'There is no current event loop in thread' errors.
"""

import sys
import os
import click
import asyncio
import logging
import threading
import traceback
from contextlib import contextmanager
from typing import Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO if not os.environ.get("LOCAL_NEWSIFIER_DEBUG") else logging.DEBUG,
    format='%(asctime)s [%(threadName)s:%(thread)d] [%(levelname)s] %(name)s: %(message)s',
)
logger = logging.getLogger(__name__)

# Thread-local storage for event loops
_thread_local = threading.local()

# Try to import diagnostic tools if available
try:
    from scripts.event_loop_diagnostics import inspect_event_loop, setup_diagnostic_hooks
    _has_diagnostics = True
    
    # Set up diagnostic hooks if requested
    if os.environ.get("LOCAL_NEWSIFIER_EVENT_LOOP_DIAGNOSTICS") == "1":
        setup_diagnostic_hooks()
        logger.info("Event loop diagnostics enabled")
except ImportError:
    _has_diagnostics = False
    
    # Create stub functions
    def inspect_event_loop(location_tag="unspecified"):
        pass


@contextmanager
def managed_event_loop():
    """Context manager that provides a guaranteed event loop for CLI commands.
    
    This ensures a valid event loop exists for the current thread and handles
    proper cleanup. It also manages thread-local storage of event loops.
    
    Yields:
        asyncio.AbstractEventLoop: The event loop for the current thread
    """
    # Get current thread ID for logging
    thread_id = threading.get_ident()
    thread_name = threading.current_thread().name
    
    # Track if we created a new loop
    created_new = False
    loop = None
    
    if _has_diagnostics:
        inspect_event_loop("managed_event_loop_start")
    
    try:
        # First try to get running loop (Python 3.7+)
        try:
            loop = asyncio.get_running_loop()
            logger.debug(f"Using existing running event loop in thread {thread_name}")
        except RuntimeError:
            # No running loop, try to get the thread's loop
            try:
                loop = asyncio.get_event_loop()
                logger.debug(f"Using existing event loop in thread {thread_name}")
            except RuntimeError:
                # No loop exists, create a new one
                logger.debug(f"Creating new event loop for thread {thread_name}")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                created_new = True
                
                # Store in thread-local storage
                _thread_local.event_loop = loop
                
                if _has_diagnostics:
                    inspect_event_loop("managed_event_loop_created")
        
        # Yield the loop for use within the context
        yield loop
        
    finally:
        if _has_diagnostics:
            inspect_event_loop("managed_event_loop_exit")


def setup_event_loop():
    """Set up an event loop for CLI commands if one doesn't exist.
    
    This is needed because some components (like fastapi-injectable dependencies)
    expect an event loop to be present, even in a CLI context.
    
    Returns:
        asyncio.AbstractEventLoop: The event loop instance
    """
    if _has_diagnostics:
        inspect_event_loop("setup_event_loop_start")
    
    try:
        # Use our context manager to get or create an event loop
        with managed_event_loop() as loop:
            logger.debug(f"Event loop set up: {id(loop)}")
            
            # Store it in a module-level thread-local variable for tracking
            if not hasattr(_thread_local, 'event_loop'):
                _thread_local.event_loop = loop
                
            return loop
    except Exception as e:
        logger.error(f"Error setting up event loop: {e}")
        raise


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """
    Local Newsifier CLI - A tool for managing local news data.
    
    This CLI provides commands for managing RSS feeds, processing articles,
    and analyzing news data.
    """
    # Setup event loop when CLI is initialized
    try:
        setup_event_loop()
    except Exception as e:
        logger.error(f"Failed to setup event loop: {e}")


def is_apify_command():
    """Check if the user is trying to run an apify command.

    This helps us avoid loading dependencies that have SQLite requirements
    when they're not needed.

    Returns:
        bool: True if the command is apify-related
    """
    # Check if 'apify' is in the command arguments
    return len(sys.argv) > 1 and (sys.argv[1] == "apify" or sys.argv[1] == "apify-config")


# Conditionally load commands to avoid unnecessary dependencies
if is_apify_command():
    # Only load the apify command if it's being used
    if sys.argv[1] == "apify":
        from local_newsifier.cli.commands.apify import apify_group
        cli.add_command(apify_group)
    elif sys.argv[1] == "apify-config":
        # Use the fixed version of apify_config if it exists, otherwise use the original
        try:
            # Try to import from the fixed module first
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
            from local_newsifier.cli.commands.apify_config_fixed import apify_config_group
            logger.debug("Using fixed apify_config_group implementation")
        except ImportError:
            # Fall back to original
            from local_newsifier.cli.commands.apify_config import apify_config_group
            logger.debug("Using original apify_config_group implementation")
        
        cli.add_command(apify_config_group)
else:
    # Load all other command groups
    from local_newsifier.cli.commands.feeds import feeds_group
    from local_newsifier.cli.commands.db import db_group
    
    # Try to use the fixed apify modules if available
    try:
        from local_newsifier.cli.commands.apify import apify_group
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from local_newsifier.cli.commands.apify_config_fixed import apify_config_group
        logger.debug("Using fixed apify_config_group implementation")
    except ImportError:
        # Fall back to original modules
        from local_newsifier.cli.commands.apify import apify_group
        from local_newsifier.cli.commands.apify_config import apify_config_group
        logger.debug("Using original apify modules")

    cli.add_command(feeds_group)
    cli.add_command(db_group)
    cli.add_command(apify_group)
    cli.add_command(apify_config_group)


def main():
    """Run the CLI application with enhanced event loop handling."""
    try:
        # Configure event loop policy
        try:
            # Only set default policy if not already set to something custom
            current_policy = asyncio.get_event_loop_policy()
            if not isinstance(current_policy, asyncio.DefaultEventLoopPolicy):
                logger.debug("Setting default event loop policy")
                asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
        except Exception as e:
            logger.warning(f"Error setting event loop policy: {e}")
        
        # Set up event loop before running CLI commands
        setup_event_loop()
        
        # Run the CLI application
        cli()
    except Exception as e:
        # Log detailed error information for debugging
        if os.environ.get("LOCAL_NEWSIFIER_DEBUG") == "1":
            logger.error(f"CLI error: {e}")
            logger.error(traceback.format_exc())
            
            # If this is an event loop error, provide more detailed diagnostics
            if "There is no current event loop" in str(e):
                logger.error("DETECTED EVENT LOOP ERROR")
                
                # Try to diagnose where the error occurred
                tb = traceback.extract_tb(sys.exc_info()[2])
                for frame in tb:
                    if 'fastapi_injectable' in frame.filename:
                        logger.error(f"fastapi-injectable issue: {frame.filename}:{frame.lineno} ({frame.name})")
                    elif 'anyio' in frame.filename:
                        logger.error(f"anyio issue: {frame.filename}:{frame.lineno} ({frame.name})")
        
        # User-friendly error message
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()