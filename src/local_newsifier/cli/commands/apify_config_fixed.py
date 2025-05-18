"""
Apify source configuration management commands with robust event loop handling.

This module provides commands for managing Apify source configurations, including:
- Listing configurations
- Adding new configurations
- Showing configuration details
- Removing configurations
- Updating configuration properties

This version includes enhanced event loop diagnostics and thread safety mechanisms
to resolve the "There is no current event loop in thread 'AnyIO worker thread'" error.
"""

import json
import sys
import click
import logging
import asyncio
import inspect
import threading
import traceback
from datetime import datetime
from tabulate import tabulate
from contextlib import contextmanager, ExitStack
from typing import Optional, Dict, Any, Generator, Callable

# Import our diagnostic tools
try:
    from scripts.event_loop_diagnostics import inspect_event_loop, cli_diagnostic_wrapper
    has_diagnostics = True
except ImportError:
    has_diagnostics = False
    # Create stub functions for when diagnostics aren't available
    def inspect_event_loop(location_tag="unspecified"):
        pass
    
    def cli_diagnostic_wrapper():
        pass

from local_newsifier.services.apify_source_config_service import ApifySourceConfigService
from local_newsifier.crud.apify_source_config import apify_source_config
from local_newsifier.services.apify_service import ApifyService

logger = logging.getLogger(__name__)

# Store thread-local event loops
_thread_local = threading.local()

def ensure_event_loop():
    """Ensure an event loop exists for the current thread.
    
    This helper function guarantees that the current thread has a valid
    event loop. If one doesn't exist, it creates a new one and sets it.
    
    Returns:
        The current event loop
    """
    if has_diagnostics:
        inspect_event_loop("ensure_event_loop_start")
    
    try:
        # First try to get the running loop
        loop = asyncio.get_running_loop()
        logger.debug(f"Using running event loop: {id(loop)}")
        return loop
    except RuntimeError:
        # No running loop, try to get the current loop
        try:
            loop = asyncio.get_event_loop()
            logger.debug(f"Using existing event loop: {id(loop)}")
            return loop
        except RuntimeError:
            # No event loop exists, create a new one
            logger.info("Creating new event loop for CLI thread")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Store in thread-local storage for easy reference
            _thread_local.event_loop = loop
            
            if has_diagnostics:
                inspect_event_loop("ensure_event_loop_created")
            
            return loop

@contextmanager
def properly_managed_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Context manager for proper event loop management.
    
    This context manager ensures an event loop exists and is properly set
    for the current thread, and manages the loop's lifecycle.
    
    Yields:
        asyncio.AbstractEventLoop: A valid event loop for the current thread
    """
    # Store the current thread ID
    thread_id = threading.get_ident()
    thread_name = threading.current_thread().name
    
    # Track if we created a new loop
    created_new = False
    loop = None
    
    if has_diagnostics:
        inspect_event_loop("properly_managed_loop_start")
    
    try:
        # Ensure event loop exists
        loop = ensure_event_loop()
        
        # Track in thread-local storage  
        if not hasattr(_thread_local, 'event_loop'):
            _thread_local.event_loop = loop
            created_new = True
            logger.debug(f"Created new event loop {id(loop)} in thread {thread_name} ({thread_id})")
        else:
            logger.debug(f"Using existing event loop {id(loop)} in thread {thread_name} ({thread_id})")
        
        # Yield the loop for use in the context
        yield loop
    
    finally:
        if has_diagnostics:
            inspect_event_loop("properly_managed_loop_exit")
        
        # Close the loop if we created a new one and it's not needed anymore
        # We might want to avoid this if the loop could be used by other code
        # For now, we'll just leave it without closing to avoid disrupting any other code


@contextmanager
def get_apify_source_config_service_direct(token: Optional[str] = None):
    """Get a directly instantiated ApifySourceConfigService to avoid async event loop issues.
    
    This helper function creates all dependencies directly instead of using
    fastapi-injectable to avoid 'no current event loop' errors in the CLI.
    
    Args:
        token: Optional Apify API token to use
    
    Yields:
        ApifySourceConfigService: Service for managing Apify source configurations
    """
    from local_newsifier.database.engine import SessionManager
    from local_newsifier.config.settings import get_settings
    
    # Use an ExitStack to properly manage all resources
    with ExitStack() as stack:
        # Ensure proper event loop management
        loop = stack.enter_context(properly_managed_loop())
        
        if has_diagnostics:
            inspect_event_loop("get_apify_source_config_service_direct:after_loop_setup")
            
        # Get session manager
        logger.debug("Creating database session")
        session_manager = SessionManager()
        session = session_manager.__enter__()
        
        # Register cleanup callback
        stack.callback(lambda: session_manager.__exit__(None, None, None))
        
        if session is None:
            logger.error("Failed to create database session")
            raise RuntimeError("Failed to create database session")
        
        try:
            logger.debug("Creating service components")
            # Create components directly (not using DI providers)
            apify_source_config_crud = apify_source_config
            
            # Create Apify service with token from settings or parameter
            settings = get_settings()
            apify_service = ApifyService(token=token or settings.APIFY_TOKEN)
            
            # Create service with session instance
            logger.debug("Creating ApifySourceConfigService")
            service = ApifySourceConfigService(
                apify_source_config_crud=apify_source_config_crud,
                apify_service=apify_service,
                session_factory=lambda: session
            )
            
            # Log debug information
            caller_frame = inspect.currentframe().f_back
            caller_info = f"{caller_frame.f_code.co_filename}:{caller_frame.f_lineno}"
            logger.debug(f"Service created and ready for use from {caller_info}")
            
            if has_diagnostics:
                inspect_event_loop("get_apify_source_config_service_direct:before_yield")
            
            yield service
            
            if has_diagnostics:
                inspect_event_loop("get_apify_source_config_service_direct:after_yield")
                
        except Exception as e:
            # Log detailed error information
            logger.error(f"Error in get_apify_source_config_service_direct: {str(e)}")
            logger.debug(f"Error details: {traceback.format_exc()}")
            
            # Check if this is an event loop error
            if "There is no current event loop" in str(e):
                logger.error("Detected event loop error - trying to recover")
                
                # Try to recover by ensuring event loop
                try:
                    ensure_event_loop()
                    logger.info("Successfully ensured event loop after error")
                except Exception as recovery_error:
                    logger.error(f"Failed to recover from event loop error: {recovery_error}")
            
            raise


@click.group(name="apify-config")
def apify_config_group():
    """Manage Apify source configurations."""
    # Ensure event loop is set up when command group is invoked
    with properly_managed_loop() as loop:
        logger.debug(f"apify-config command group invoked with event loop {id(loop)}")


@apify_config_group.command(name="list")
@click.option("--active-only", is_flag=True, help="Show only active configurations")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.option("--limit", type=int, default=100, help="Maximum number of configurations to display")
@click.option("--skip", type=int, default=0, help="Number of configurations to skip")
@click.option("--source-type", help="Filter by source type (e.g., news, blog)")
@click.option("--debug", is_flag=True, help="Enable additional debug logging")
def list_configs(active_only, json_output, limit, skip, source_type, debug):
    """List all Apify source configurations with optional filtering."""
    if debug and has_diagnostics:
        cli_diagnostic_wrapper()
    
    # Use an ExitStack for proper resource management
    with ExitStack() as stack:
        # Ensure event loop exists
        loop = stack.enter_context(properly_managed_loop())
        logger.debug(f"list_configs command using event loop {id(loop)}")
        
        try:
            # Get the service with proper event loop handling
            logger.debug("Getting ApifySourceConfigService")
            with get_apify_source_config_service_direct() as apify_source_config_service:
                logger.debug("Retrieving configs from service")
                
                # Get configs based on filters
                configs_dict = apify_source_config_service.list_configs(
                    skip=skip, 
                    limit=limit, 
                    active_only=active_only, 
                    source_type=source_type
                )
            
                if json_output:
                    click.echo(json.dumps(configs_dict, indent=2, default=str))
                    return
                
                if not configs_dict:
                    click.echo("No Apify source configurations found.")
                    return
                
                # Format data for table
                table_data = []
                for config in configs_dict:
                    last_run = config.get("last_run_at")
                    if last_run:
                        # Handle both datetime and string representations
                        if isinstance(last_run, str):
                            try:
                                last_run = datetime.fromisoformat(last_run).strftime("%Y-%m-%d %H:%M")
                            except:
                                # Handle potential format issues
                                pass
                    
                    # Truncate input_configuration if it's too long
                    input_config = str(config.get("input_configuration", {}))
                    if len(input_config) > 30:
                        input_config = input_config[:27] + "..."
                    
                    table_data.append([
                        config["id"],
                        config["name"],
                        config["actor_id"],
                        config["source_type"],
                        "✓" if config["is_active"] else "✗",
                        last_run or "Never",
                        input_config
                    ])
                
                # Display table
                headers = ["ID", "Name", "Actor ID", "Type", "Active", "Last Run", "Config"]
                click.echo(tabulate(table_data, headers=headers, tablefmt="simple"))
        except Exception as e:
            # Check for specific error types and provide helpful guidance
            if "There is no current event loop" in str(e):
                error_msg = (
                    "Event loop error detected. This is likely due to an issue with fastapi-injectable "
                    "or anyio in a CLI context. Try running with --debug for more diagnostics."
                )
                click.echo(click.style(error_msg, fg="red"), err=True)
                
                if debug:
                    click.echo(click.style(f"Error details: {traceback.format_exc()}", fg="yellow"), err=True)
            else:
                click.echo(click.style(f"Error listing configurations: {str(e)}", fg="red"), err=True)


@apify_config_group.command(name="add")
@click.option("--name", required=True, help="Configuration name")
@click.option("--actor-id", required=True, help="Apify actor ID")
@click.option("--source-type", required=True, help="Source type (e.g., news, blog)")
@click.option("--source-url", help="Source URL (optional)")
@click.option("--schedule", help="Cron schedule expression (optional)")
@click.option("--input", "-i", help="JSON string or file path for actor input configuration")
@click.option("--debug", is_flag=True, help="Enable additional debug logging")
def add_config(name, actor_id, source_type, source_url, schedule, input, debug):
    """Add a new Apify source configuration."""
    if debug and has_diagnostics:
        cli_diagnostic_wrapper()
    
    # Ensure event loop is properly managed
    with properly_managed_loop() as loop:
        logger.debug(f"add_config command using event loop {id(loop)}")
        
        # Get the service using direct instantiation to avoid event loop issues
        with get_apify_source_config_service_direct() as apify_source_config_service:
            # Parse input configuration if provided
            input_configuration = None
            if input:
                if input.startswith("{") or input.startswith("["):
                    try:
                        input_configuration = json.loads(input)
                    except json.JSONDecodeError:
                        click.echo(click.style("Error: Input must be valid JSON", fg="red"), err=True)
                        return
                elif input.endswith(".json") and input.find("/") != -1:
                    # Looks like a file path
                    try:
                        with open(input, "r") as f:
                            input_configuration = json.load(f)
                        click.echo(f"Loaded input configuration from file: {input}")
                    except Exception as e:
                        click.echo(
                            click.style(f"Error loading input file: {str(e)}", fg="red"),
                            err=True,
                        )
                        return
            
            try:
                config = apify_source_config_service.create_config(
                    name=name,
                    actor_id=actor_id,
                    source_type=source_type,
                    source_url=source_url,
                    schedule=schedule,
                    input_configuration=input_configuration
                )
                
                click.echo(f"Apify source configuration added successfully with ID: {config['id']}")
                click.echo(f"Name: {config['name']}")
                click.echo(f"Actor ID: {config['actor_id']}")
                click.echo(f"Source Type: {config['source_type']}")
            except Exception as e:
                click.echo(click.style(f"Error adding configuration: {str(e)}", fg="red"), err=True)


@apify_config_group.command(name="show")
@click.argument("id", type=int, required=True)
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.option("--debug", is_flag=True, help="Enable additional debug logging")
def show_config(id, json_output, debug):
    """Show Apify source configuration details."""
    if debug and has_diagnostics:
        cli_diagnostic_wrapper()
    
    # Ensure event loop is properly managed
    with properly_managed_loop() as loop:
        logger.debug(f"show_config command using event loop {id(loop)}")
        
        try:
            with get_apify_source_config_service_direct() as apify_source_config_service:
                config = apify_source_config_service.get_config(id)
                if not config:
                    click.echo(click.style(f"Error: Configuration with ID {id} not found", fg="red"), err=True)
                    return
                
                if json_output:
                    click.echo(json.dumps(config, indent=2, default=str))
                    return
                
                # Display config details
                click.echo(click.style(f"Configuration #{config['id']}: {config['name']}", fg="green", bold=True))
                click.echo(f"Actor ID: {config['actor_id']}")
                click.echo(f"Source Type: {config['source_type']}")
                if config['source_url']:
                    click.echo(f"Source URL: {config['source_url']}")
                click.echo(f"Active: {'Yes' if config['is_active'] else 'No'}")
                
                if config['schedule']:
                    click.echo(f"Schedule: {config['schedule']}")
                
                last_run = config['last_run_at']
                if last_run:
                    click.echo(f"Last Run: {last_run}")
                else:
                    click.echo("Last Run: Never")
                
                click.echo("\nInput Configuration:")
                click.echo(json.dumps(config['input_configuration'], indent=2))
                
                created_at = config['created_at']
                click.echo(f"\nCreated At: {created_at}")
        except Exception as e:
            click.echo(click.style(f"Error retrieving configuration: {str(e)}", fg="red"), err=True)


@apify_config_group.command(name="remove")
@click.argument("id", type=int, required=True)
@click.option("--force", is_flag=True, help="Skip confirmation")
@click.option("--debug", is_flag=True, help="Enable additional debug logging")
def remove_config(id, force, debug):
    """Remove an Apify source configuration."""
    if debug and has_diagnostics:
        cli_diagnostic_wrapper()
    
    # Ensure event loop is properly managed
    with properly_managed_loop() as loop:
        logger.debug(f"remove_config command using event loop {id(loop)}")
        
        # Get the service using direct instantiation to avoid event loop issues
        with get_apify_source_config_service_direct() as apify_source_config_service:
            try:
                config = apify_source_config_service.get_config(id)
                if not config:
                    click.echo(click.style(f"Error: Configuration with ID {id} not found", fg="red"), err=True)
                    return
                
                if not force:
                    if not click.confirm(f"Are you sure you want to remove configuration '{config['name']}' (ID: {id})?"):
                        click.echo("Operation canceled.")
                        return
                
                result = apify_source_config_service.remove_config(id)
                if result:
                    click.echo(f"Configuration '{config['name']}' (ID: {id}) removed successfully.")
                else:
                    click.echo(click.style(f"Error removing configuration with ID {id}", fg="red"), err=True)
            except Exception as e:
                click.echo(click.style(f"Error removing configuration: {str(e)}", fg="red"), err=True)


@apify_config_group.command(name="update")
@click.argument("id", type=int, required=True)
@click.option("--name", help="New configuration name")
@click.option("--actor-id", help="New actor ID")
@click.option("--source-type", help="New source type")
@click.option("--source-url", help="New source URL")
@click.option("--schedule", help="New schedule expression")
@click.option("--active/--inactive", help="Set configuration active or inactive")
@click.option("--input", "-i", help="JSON string or file path for actor input configuration")
@click.option("--debug", is_flag=True, help="Enable additional debug logging")
def update_config(id, name, actor_id, source_type, source_url, schedule, active, input, debug):
    """Update Apify source configuration properties."""
    if debug and has_diagnostics:
        cli_diagnostic_wrapper()
    
    # Ensure event loop is properly managed
    with properly_managed_loop() as loop:
        logger.debug(f"update_config command using event loop {id(loop)}")
        
        # Get the service using direct instantiation to avoid event loop issues
        with get_apify_source_config_service_direct() as apify_source_config_service:
            try:
                # Check if at least one property to update was provided
                if all(v is None for v in [name, actor_id, source_type, source_url, schedule, active, input]):
                    click.echo("No properties specified for update. Use --name, --actor-id, etc.")
                    return
                
                # Parse input configuration if provided
                input_configuration = None
                if input:
                    if input.startswith("{") or input.startswith("["):
                        try:
                            input_configuration = json.loads(input)
                        except json.JSONDecodeError:
                            click.echo(click.style("Error: Input must be valid JSON", fg="red"), err=True)
                            return
                    elif input.endswith(".json") and input.find("/") != -1:
                        # Looks like a file path
                        try:
                            with open(input, "r") as f:
                                input_configuration = json.load(f)
                            click.echo(f"Loaded input configuration from file: {input}")
                        except Exception as e:
                            click.echo(
                                click.style(f"Error loading input file: {str(e)}", fg="red"),
                                err=True,
                            )
                            return
                
                # Update config
                updated_config = apify_source_config_service.update_config(
                    config_id=id,
                    name=name,
                    actor_id=actor_id,
                    source_type=source_type,
                    source_url=source_url,
                    schedule=schedule,
                    is_active=active,
                    input_configuration=input_configuration
                )
                
                if not updated_config:
                    click.echo(click.style(f"Error: Configuration with ID {id} not found", fg="red"), err=True)
                    return
                    
                click.echo(f"Configuration '{updated_config['name']}' (ID: {id}) updated successfully.")
            except Exception as e:
                click.echo(click.style(f"Error updating configuration: {str(e)}", fg="red"), err=True)


@apify_config_group.command(name="run")
@click.argument("id", type=int, required=True)
@click.option("--output", "-o", help="Save output to file")
@click.option("--debug", is_flag=True, help="Enable additional debug logging")
def run_config(id, output, debug):
    """Run an Apify actor based on a source configuration.
    
    This command will execute the Apify actor associated with the configuration
    using the stored input parameters.
    
    ID is the ID of the configuration to run.
    
    Examples:
        nf apify-config run 1
        nf apify-config run 2 --output result.json
    """
    if debug and has_diagnostics:
        cli_diagnostic_wrapper()
    
    # Ensure event loop is properly managed
    with properly_managed_loop() as loop:
        logger.debug(f"run_config command using event loop {id(loop)}")
        
        # Get the service using direct instantiation to avoid event loop issues
        with get_apify_source_config_service_direct() as apify_source_config_service:
            try:
                # Run the configuration
                result = apify_source_config_service.run_configuration(id)
                
                if result["status"] == "success":
                    click.echo(click.style("✓ Actor run completed successfully!", fg="green"))
                    click.echo(f"Configuration: {result['config_name']} (ID: {result['config_id']})")
                    click.echo(f"Actor ID: {result['actor_id']}")
                    click.echo(f"Run ID: {result['run_id']}")
                    
                    # Output dataset info if available
                    if "dataset_id" in result and result["dataset_id"]:
                        click.echo(f"Dataset ID: {result['dataset_id']}")
                        click.echo(f"To retrieve the data: nf apify get-dataset {result['dataset_id']}")
                    
                    # Save or display the results
                    if output:
                        with open(output, "w") as f:
                            json.dump(result, f, indent=2)
                        click.echo(f"Output saved to {output}")
                else:
                    click.echo(click.style("✗ Actor run failed.", fg="red"), err=True)
                    click.echo(click.style(f"Error: {result.get('message', 'Unknown error')}", fg="red"), err=True)
                    
            except Exception as e:
                click.echo(click.style(f"Error running configuration: {str(e)}", fg="red"), err=True)