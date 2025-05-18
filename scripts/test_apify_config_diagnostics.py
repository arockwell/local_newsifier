#!/usr/bin/env python
"""
Test script to run the apify-config command with event loop diagnostics.

This script executes the 'nf apify-config list' command that has been
experiencing event loop issues, with added instrumentation to trace the source
of the problem.

Usage:
    python scripts/test_apify_config_diagnostics.py
"""

import os
import sys
import subprocess
import threading
import asyncio
import logging
from importlib import import_module

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the necessary path to find the local_newsifier package
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

# Import the diagnostic tools
from scripts.event_loop_diagnostics import (
    setup_diagnostic_hooks, 
    inspect_event_loop, 
    debug_threads,
    install_event_loop_monitor
)

def run_injected_cli():
    """Run the CLI with event loop diagnostics injected."""
    # Set up diagnostic hooks
    logger.info("Setting up event loop diagnostics...")
    setup_diagnostic_hooks()
    
    # Start event loop monitor
    stop_monitor = install_event_loop_monitor()
    
    try:
        # Import the CLI modules
        logger.info("Importing CLI modules...")
        from local_newsifier.cli.main import cli, setup_event_loop
        from local_newsifier.cli.commands.apify_config import (
            apify_config_group, 
            get_apify_source_config_service_direct
        )
        
        # Check initial event loop state
        inspect_event_loop("before_cli_setup")
        
        # Instrument the CLI setup_event_loop function
        original_setup_event_loop = setup_event_loop
        
        def instrumented_setup_event_loop():
            """Instrumented version of setup_event_loop to track loop creation."""
            inspect_event_loop("before_setup_event_loop")
            try:
                loop = original_setup_event_loop()
                logger.info(f"setup_event_loop created loop: {id(loop)}")
                inspect_event_loop("after_setup_event_loop")
                return loop
            except Exception as e:
                logger.error(f"Error in setup_event_loop: {e}")
                raise
        
        # Instrument the get_apify_source_config_service_direct context manager
        original_get_service = get_apify_source_config_service_direct
        
        # Replace with instrumented versions
        from local_newsifier.cli.main import setup_event_loop as main_setup_event_loop
        main_setup_event_loop.__code__ = instrumented_setup_event_loop.__code__
        
        # Instrument the list_configs command
        @apify_config_group.command(name="list_debug", help="Instrumented version of list command")
        def list_configs_debug():
            """Instrumented version of the list command with diagnostics."""
            inspect_event_loop("before_list_configs")
            
            try:
                # Create a diagnostic context to show the event loop state
                logger.info("Attempting to get service with diagnostics...")
                with original_get_service() as service:
                    inspect_event_loop("inside_get_service")
                    
                    # Try to list configs
                    configs = service.list_configs()
                    logger.info(f"Got {len(configs)} configurations")
                    
                    # Print some info
                    for config in configs[:5]:  # Limit to first 5
                        logger.info(f"Config: {config['id']} - {config['name']}")
                
                inspect_event_loop("after_service_usage")
            except Exception as e:
                logger.error(f"Error in list_configs_debug: {e}")
                
                # Print detailed error information
                import traceback
                logger.error(f"Detailed error:\n{traceback.format_exc()}")
                
                # Try to diagnose the specific error
                if "There is no current event loop in thread" in str(e):
                    logger.error("DIAGNOSIS: This is the 'no current event loop' error we're investigating")
                    
                    # Try to determine where the error occurred
                    tb = traceback.extract_tb(sys.exc_info()[2])
                    for frame in tb:
                        if 'fastapi_injectable' in frame.filename:
                            logger.error(f"Error traced to fastapi-injectable: {frame.filename}:{frame.lineno}")
                        elif 'anyio' in frame.filename:
                            logger.error(f"Error traced to anyio: {frame.filename}:{frame.lineno}")
                
                # Try to recover by creating a new event loop
                try:
                    logger.info("Attempting to recover by creating a new event loop...")
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # Check if we have an event loop now
                    current_loop = asyncio.get_event_loop()
                    logger.info(f"Successfully created new event loop: {id(current_loop)}")
                except Exception as e2:
                    logger.error(f"Recovery failed: {e2}")
        
        # Add instrumented command to CLI
        cli.add_command(list_configs_debug)
        
        # Check CLI command state
        inspect_event_loop("before_cli_invocation")
        
        # Show all current threads
        debug_threads()
        
        # Manually invoke CLI with args
        logger.info("Running CLI with 'apify-config list_debug'...")
        
        # Create an event loop for the CLI
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Set command-line arguments
        sys.argv = ['nf', 'apify-config', 'list_debug']
        
        # Run the CLI
        cli()
        
        # Check final state
        inspect_event_loop("after_cli_completion")
        debug_threads()
        
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        # Stop the monitor
        stop_monitor.set()

def run_subprocess_cli():
    """Run the CLI in a subprocess with environmental variables for logging."""
    # Set environment variables to enable logging
    env = os.environ.copy()
    env['PYTHONPATH'] = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
    env['LOCAL_NEWSIFIER_DEBUG'] = '1'
    env['LOCAL_NEWSIFIER_EVENT_LOOP_DIAGNOSTICS'] = '1'
    
    # Run the command
    logger.info("Running CLI in subprocess: nf apify-config list")
    proc = subprocess.Popen(
        ['nf', 'apify-config', 'list'], 
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    
    # Get output
    stdout, stderr = proc.communicate()
    
    # Log results
    logger.info(f"CLI subprocess exit code: {proc.returncode}")
    if stdout:
        logger.info(f"CLI subprocess stdout:\n{stdout}")
    if stderr:
        logger.error(f"CLI subprocess stderr:\n{stderr}")
    
    return proc.returncode

def main():
    """Main entry point to run diagnostics on apify-config CLI command."""
    logger.info("Running apify-config CLI diagnostics")
    
    # First check if we can patch the modules and run directly
    try:
        logger.info("Attempting to run with injected diagnostics...")
        run_injected_cli()
    except Exception as e:
        logger.error(f"Injected CLI run failed: {e}")
    
    # Also try running as a subprocess
    logger.info("\n\nAttempting to run CLI as subprocess...")
    exit_code = run_subprocess_cli()
    
    logger.info(f"Diagnostics completed with subprocess exit code: {exit_code}")

if __name__ == "__main__":
    main()