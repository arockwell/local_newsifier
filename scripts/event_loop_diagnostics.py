"""
Event Loop Diagnostic Tool for Local Newsifier CLI

This script provides diagnostic tools for troubleshooting asyncio event loop issues 
in the Local Newsifier CLI, particularly with the apify-config command.

To use:
1. Import the functions from this module in the modules experiencing issues
2. Call setup_diagnostic_hooks() at the start of the program
3. Use the inspect_event_loop() function to check event loop state at key points
4. Add the MonkeyPatchEventLoop class to intercept and trace asyncio operations

Usage example:
```python
from scripts.event_loop_diagnostics import setup_diagnostic_hooks, inspect_event_loop

# At the start of your CLI entry point
setup_diagnostic_hooks()

# Before running a command that may fail
inspect_event_loop("before_apify_config_command")
```

This tool will help identify where event loops are created, accessed, and potentially 
lost across thread boundaries or due to lifecycle issues with fastapi-injectable.
"""

import os
import sys
import asyncio
import inspect
import threading
import traceback
import logging
import functools
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from contextlib import contextmanager

# Configure logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(log_dir, exist_ok=True)

# Create custom detailed formatter
formatter = logging.Formatter(
    '%(asctime)s [%(threadName)s:%(thread)d] [%(levelname)s] '
    '%(module)s.%(funcName)s:%(lineno)d - %(message)s'
)

# Setup file handler for detailed logs
log_file = os.path.join(log_dir, f"event_loop_diagnostics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)

# Setup console handler for higher-level logs
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
console_handler.setLevel(logging.INFO)

# Create logger
logger = logging.getLogger("event_loop_diagnostics")
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Global storage for event loop tracking
_event_loop_registry = {}
_thread_local = threading.local()
_call_stack_history = []
_original_functions = {}
_thread_registry = {}


def log_event_loop_creation(loop, location):
    """Log creation of a new event loop with stack trace and thread info."""
    thread_id = threading.get_ident()
    thread_name = threading.current_thread().name
    
    _event_loop_registry[id(loop)] = {
        'loop': loop,
        'created_at': datetime.now(),
        'created_by': location,
        'thread_id': thread_id,
        'thread_name': thread_name,
        'stack_trace': traceback.format_stack(),
    }
    
    # Store the loop in thread-local storage
    if not hasattr(_thread_local, 'loops'):
        _thread_local.loops = []
    
    _thread_local.loops.append(loop)
    
    # Also track in thread registry
    if thread_id not in _thread_registry:
        _thread_registry[thread_id] = {
            'name': thread_name,
            'loops': []
        }
    _thread_registry[thread_id]['loops'].append(id(loop))
    
    logger.debug(
        f"Event loop {id(loop)} created in thread {thread_name} ({thread_id}) "
        f"at {location}"
    )


def log_event_loop_closure(loop):
    """Log when an event loop is closed."""
    thread_id = threading.get_ident()
    thread_name = threading.current_thread().name
    
    if id(loop) in _event_loop_registry:
        loop_info = _event_loop_registry[id(loop)]
        created_by = loop_info.get('created_by', 'unknown')
        created_thread = loop_info.get('thread_name', 'unknown')
        
        logger.debug(
            f"Event loop {id(loop)} created by {created_by} in thread {created_thread} "
            f"is being closed in thread {thread_name} ({thread_id})"
        )
    else:
        logger.warning(
            f"Untracked event loop {id(loop)} is being closed in thread {thread_name} ({thread_id})"
        )


def log_call_stack(function_name, args=None, kwargs=None, result=None, exception=None):
    """Log function call with arguments and result/exception."""
    thread_id = threading.get_ident()
    thread_name = threading.current_thread().name
    timestamp = datetime.now()
    
    # Get the current stack frame
    frame = inspect.currentframe().f_back.f_back  # Go back two frames to get the caller's frame
    
    # Build call information
    call_info = {
        'timestamp': timestamp,
        'function': function_name,
        'thread_id': thread_id,
        'thread_name': thread_name,
        'file': frame.f_code.co_filename,
        'line': frame.f_lineno,
        'args': args,
        'kwargs': kwargs,
        'result': repr(result) if result is not None else None,
        'exception': repr(exception) if exception is not None else None,
        'stack': traceback.format_stack()
    }
    
    # Add to history and log
    _call_stack_history.append(call_info)
    
    # Log the call
    if exception:
        logger.error(
            f"Function {function_name} failed in thread {thread_name} ({thread_id}): {exception}"
        )
    else:
        logger.debug(
            f"Function {function_name} called in thread {thread_name} ({thread_id})"
        )


def monkey_patch_asyncio():
    """Monkey patch asyncio functions to track event loop usage."""
    # Store original functions
    _original_functions['new_event_loop'] = asyncio.new_event_loop
    _original_functions['get_event_loop'] = asyncio.get_event_loop
    _original_functions['set_event_loop'] = asyncio.set_event_loop
    
    if hasattr(asyncio, 'get_running_loop'):
        _original_functions['get_running_loop'] = asyncio.get_running_loop
    
    # Replace with instrumented versions
    @functools.wraps(asyncio.new_event_loop)
    def instrumented_new_event_loop():
        """Instrumented version of asyncio.new_event_loop()."""
        try:
            # Call original function
            loop = _original_functions['new_event_loop']()
            
            # Get caller info
            frame = inspect.currentframe().f_back
            caller_info = f"{frame.f_code.co_filename}:{frame.f_lineno}"
            
            # Log creation
            log_event_loop_creation(loop, caller_info)
            log_call_stack('asyncio.new_event_loop', result=loop)
            
            # Monkey patch the loop's close method
            original_close = loop.close
            
            @functools.wraps(original_close)
            def instrumented_close():
                """Instrumented version of loop.close()."""
                try:
                    log_event_loop_closure(loop)
                    log_call_stack('loop.close')
                    return original_close()
                except Exception as e:
                    log_call_stack('loop.close', exception=e)
                    raise
                
            loop.close = instrumented_close
            
            return loop
        except Exception as e:
            log_call_stack('asyncio.new_event_loop', exception=e)
            raise
    
    @functools.wraps(asyncio.get_event_loop)
    def instrumented_get_event_loop():
        """Instrumented version of asyncio.get_event_loop()."""
        try:
            # Call original function
            loop = _original_functions['get_event_loop']()
            
            # Log usage
            log_call_stack('asyncio.get_event_loop', result=loop)
            
            return loop
        except Exception as e:
            log_call_stack('asyncio.get_event_loop', exception=e)
            raise
    
    @functools.wraps(asyncio.set_event_loop)
    def instrumented_set_event_loop(loop):
        """Instrumented version of asyncio.set_event_loop()."""
        try:
            # Log usage
            log_call_stack('asyncio.set_event_loop', args=[loop])
            
            # Call original function
            return _original_functions['set_event_loop'](loop)
        except Exception as e:
            log_call_stack('asyncio.set_event_loop', args=[loop], exception=e)
            raise
    
    # Apply monkey patches
    asyncio.new_event_loop = instrumented_new_event_loop
    asyncio.get_event_loop = instrumented_get_event_loop
    asyncio.set_event_loop = instrumented_set_event_loop
    
    # Patch get_running_loop if it exists (Python 3.7+)
    if 'get_running_loop' in _original_functions:
        @functools.wraps(asyncio.get_running_loop)
        def instrumented_get_running_loop():
            """Instrumented version of asyncio.get_running_loop()."""
            try:
                # Call original function
                loop = _original_functions['get_running_loop']()
                
                # Log usage
                log_call_stack('asyncio.get_running_loop', result=loop)
                
                return loop
            except Exception as e:
                log_call_stack('asyncio.get_running_loop', exception=e)
                raise
        
        asyncio.get_running_loop = instrumented_get_running_loop


def monkey_patch_anyio():
    """Attempt to monkey patch AnyIO functions to track event loop usage."""
    try:
        import anyio
        from anyio.abc import CapacityLimiter
        
        # Check if we can access anyio's event loop backends
        if hasattr(anyio, '_backends'):
            logger.info("Instrumenting AnyIO backends")
            
            # Track original methods
            for backend_name, backend_mod in anyio._backends.items():
                if hasattr(backend_mod, 'get_all_backends'):
                    _original_functions[f'anyio.{backend_name}.get_all_backends'] = backend_mod.get_all_backends
                
                if hasattr(backend_mod, 'run'):
                    _original_functions[f'anyio.{backend_name}.run'] = backend_mod.run
                
                if hasattr(backend_mod, 'create_event_loop'):
                    _original_functions[f'anyio.{backend_name}.create_event_loop'] = backend_mod.create_event_loop
            
            # Monkey patch all backends
            for backend_name, backend_mod in anyio._backends.items():
                # Patch create_event_loop if it exists
                if hasattr(backend_mod, 'create_event_loop'):
                    original_create_event_loop = backend_mod.create_event_loop
                    
                    @functools.wraps(original_create_event_loop)
                    def instrumented_create_event_loop(*args, **kwargs):
                        try:
                            # Call original function
                            result = original_create_event_loop(*args, **kwargs)
                            
                            # Log usage
                            log_call_stack(f'anyio.{backend_name}.create_event_loop', 
                                          args=args, kwargs=kwargs, result=result)
                            
                            return result
                        except Exception as e:
                            log_call_stack(f'anyio.{backend_name}.create_event_loop', 
                                          args=args, kwargs=kwargs, exception=e)
                            raise
                    
                    backend_mod.create_event_loop = instrumented_create_event_loop
                
                # Patch run if it exists
                if hasattr(backend_mod, 'run'):
                    original_run = backend_mod.run
                    
                    @functools.wraps(original_run)
                    def instrumented_run(func, *args, **kwargs):
                        try:
                            # Log before run
                            log_call_stack(f'anyio.{backend_name}.run', 
                                          args=[func, *args], kwargs=kwargs)
                            
                            # Call original function
                            return original_run(func, *args, **kwargs)
                        except Exception as e:
                            log_call_stack(f'anyio.{backend_name}.run', 
                                          args=[func, *args], kwargs=kwargs, exception=e)
                            raise
                    
                    backend_mod.run = instrumented_run
        
        # Instrument top-level anyio functions
        if hasattr(anyio, 'run'):
            _original_functions['anyio.run'] = anyio.run
            
            @functools.wraps(anyio.run)
            def instrumented_anyio_run(func, *args, **kwargs):
                try:
                    # Log before run
                    log_call_stack('anyio.run', args=[func, *args], kwargs=kwargs)
                    
                    # Call original function
                    return _original_functions['anyio.run'](func, *args, **kwargs)
                except Exception as e:
                    log_call_stack('anyio.run', args=[func, *args], kwargs=kwargs, exception=e)
                    raise
            
            anyio.run = instrumented_anyio_run
        
        logger.info("AnyIO instrumentation complete")
    
    except ImportError:
        logger.info("AnyIO not found, skipping instrumentation")
    except Exception as e:
        logger.error(f"Error instrumenting AnyIO: {e}")


def monkey_patch_fastapi_injectable():
    """Monkey patch fastapi-injectable functions to track event loop usage."""
    try:
        import fastapi_injectable
        
        # Store original functions
        if hasattr(fastapi_injectable, 'register_app'):
            _original_functions['fastapi_injectable.register_app'] = fastapi_injectable.register_app
        
        if hasattr(fastapi_injectable, 'get_injected_obj'):
            _original_functions['fastapi_injectable.get_injected_obj'] = fastapi_injectable.get_injected_obj
        
        # Replace with instrumented versions
        if 'fastapi_injectable.register_app' in _original_functions:
            @functools.wraps(fastapi_injectable.register_app)
            async def instrumented_register_app(app, *args, **kwargs):
                """Instrumented version of fastapi_injectable.register_app()."""
                try:
                    # Log usage
                    log_call_stack('fastapi_injectable.register_app', args=[app, *args], kwargs=kwargs)
                    
                    # Create stack trace for debugging
                    stack_trace = ''.join(traceback.format_stack())
                    logger.debug(f"register_app called with stack trace:\n{stack_trace}")
                    
                    # Log current event loop state
                    try:
                        current_loop = asyncio.get_event_loop()
                        logger.debug(f"Current event loop before register_app: {id(current_loop)}")
                    except RuntimeError as e:
                        logger.warning(f"No event loop available before register_app: {e}")
                    
                    # Call original function
                    result = await _original_functions['fastapi_injectable.register_app'](app, *args, **kwargs)
                    
                    # Log result
                    log_call_stack('fastapi_injectable.register_app', 
                                  args=[app, *args], kwargs=kwargs, result=result)
                    
                    return result
                except Exception as e:
                    log_call_stack('fastapi_injectable.register_app', 
                                  args=[app, *args], kwargs=kwargs, exception=e)
                    raise
            
            fastapi_injectable.register_app = instrumented_register_app
        
        if 'fastapi_injectable.get_injected_obj' in _original_functions:
            @functools.wraps(fastapi_injectable.get_injected_obj)
            async def instrumented_get_injected_obj(obj, *args, **kwargs):
                """Instrumented version of fastapi_injectable.get_injected_obj()."""
                try:
                    # Log usage
                    log_call_stack('fastapi_injectable.get_injected_obj', args=[obj, *args], kwargs=kwargs)
                    
                    # Create stack trace for debugging
                    stack_trace = ''.join(traceback.format_stack())
                    logger.debug(f"get_injected_obj called with stack trace:\n{stack_trace}")
                    
                    # Log current event loop state
                    try:
                        current_loop = asyncio.get_event_loop()
                        logger.debug(f"Current event loop before get_injected_obj: {id(current_loop)}")
                    except RuntimeError as e:
                        logger.warning(f"No event loop available before get_injected_obj: {e}")
                    
                    # Call original function
                    result = await _original_functions['fastapi_injectable.get_injected_obj'](obj, *args, **kwargs)
                    
                    # Log result
                    log_call_stack('fastapi_injectable.get_injected_obj', 
                                  args=[obj, *args], kwargs=kwargs, result=result)
                    
                    return result
                except Exception as e:
                    log_call_stack('fastapi_injectable.get_injected_obj', 
                                  args=[obj, *args], kwargs=kwargs, exception=e)
                    raise
            
            fastapi_injectable.get_injected_obj = instrumented_get_injected_obj
        
        logger.info("FastAPI-Injectable instrumentation complete")
    
    except ImportError:
        logger.info("FastAPI-Injectable not found, skipping instrumentation")
    except Exception as e:
        logger.error(f"Error instrumenting FastAPI-Injectable: {e}")


class MonkeyPatchEventLoop:
    """Context manager to monkey patch and restore asyncio event loop methods."""
    
    def __init__(self):
        self.original_new_event_loop = asyncio.new_event_loop
        self.original_get_event_loop = asyncio.get_event_loop
        self.original_set_event_loop = asyncio.set_event_loop
        self.original_get_running_loop = getattr(asyncio, 'get_running_loop', None)
        self.patched = False
    
    def __enter__(self):
        """Apply monkey patches on entry."""
        if not self.patched:
            monkey_patch_asyncio()
            monkey_patch_anyio()
            monkey_patch_fastapi_injectable()
            self.patched = True
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore original functions on exit."""
        # Don't restore the originals - we want the instrumentation to persist
        # across the application lifetime for maximum diagnostics
        return False


@contextmanager
def event_loop_diagnostics():
    """Context manager that sets up diagnostics for asyncio event loops."""
    with MonkeyPatchEventLoop():
        yield


def inspect_event_loop(location_tag="unspecified"):
    """Inspect the current state of event loops for the calling thread.
    
    This function can be called at key points in your code to log the state
    of event loops. It will show which event loops are available and which
    thread they belong to.
    
    Args:
        location_tag: A string tag to identify where this inspection was called from
    
    Returns:
        A dict with diagnostic information about the current event loop state
    """
    thread_id = threading.get_ident()
    thread_name = threading.current_thread().name
    
    logger.info(f"=== EVENT LOOP INSPECTION at {location_tag} ===")
    logger.info(f"Current thread: {thread_name} ({thread_id})")
    
    # Try to get current event loop
    current_loop = None
    try:
        # Try get_running_loop first (Python 3.7+)
        if hasattr(asyncio, 'get_running_loop'):
            try:
                current_loop = asyncio.get_running_loop()
                logger.info(f"Current running loop: {id(current_loop)}")
            except RuntimeError:
                logger.info("No running event loop in current thread")
        
        # Fall back to get_event_loop
        try:
            loop = asyncio.get_event_loop()
            if current_loop is None:
                current_loop = loop
                logger.info(f"Current loop from get_event_loop(): {id(loop)}")
            elif id(loop) != id(current_loop):
                logger.warning(
                    f"get_event_loop() returned different loop ({id(loop)}) "
                    f"than get_running_loop() ({id(current_loop)})"
                )
        except RuntimeError as e:
            logger.warning(f"Error getting event loop: {e}")
    except Exception as e:
        logger.error(f"Error inspecting event loop: {e}")
    
    # Check thread-local storage
    thread_loops = getattr(_thread_local, 'loops', [])
    if thread_loops:
        logger.info(f"Thread-local loops: {[id(l) for l in thread_loops]}")
    else:
        logger.info("No thread-local loops found")
    
    # Check global registry for loops created in this thread
    thread_loops_from_registry = []
    for loop_id, info in _event_loop_registry.items():
        if info['thread_id'] == thread_id:
            thread_loops_from_registry.append(loop_id)
    
    if thread_loops_from_registry:
        logger.info(f"Loops created in this thread: {thread_loops_from_registry}")
    else:
        logger.info("No loops created in this thread")
    
    # Collect diagnostic info
    diagnostic_info = {
        'timestamp': datetime.now(),
        'location': location_tag,
        'thread': {
            'id': thread_id,
            'name': thread_name
        },
        'current_loop': id(current_loop) if current_loop else None,
        'thread_local_loops': [id(l) for l in thread_loops],
        'loops_created_in_thread': thread_loops_from_registry,
        'stack_trace': traceback.format_stack()
    }
    
    # Log to debug
    logger.debug(f"Event loop inspection at {location_tag}: {diagnostic_info}")
    
    return diagnostic_info


def get_thread_info():
    """Get information about all threads and their event loops."""
    current_thread_id = threading.get_ident()
    current_thread_name = threading.current_thread().name
    
    all_threads = {t.ident: t.name for t in threading.enumerate()}
    
    thread_info = {
        'current_thread': {
            'id': current_thread_id,
            'name': current_thread_name
        },
        'all_threads': all_threads,
        'thread_registry': _thread_registry,
        'event_loops': {
            loop_id: {
                'created_at': info['created_at'],
                'created_by': info['created_by'],
                'thread_id': info['thread_id'],
                'thread_name': info['thread_name']
            } for loop_id, info in _event_loop_registry.items()
        }
    }
    
    return thread_info


def log_function_diagnostics(func):
    """Decorator to log function entry/exit with event loop state."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__qualname__
        thread_id = threading.get_ident()
        thread_name = threading.current_thread().name
        
        logger.debug(f"Entering {func_name} in thread {thread_name} ({thread_id})")
        
        # Check event loop before
        try:
            loop = asyncio.get_event_loop()
            logger.debug(f"Event loop before {func_name}: {id(loop)}")
        except RuntimeError as e:
            logger.debug(f"No event loop before {func_name}: {e}")
        
        try:
            # Call the original function
            result = func(*args, **kwargs)
            
            # Check event loop after
            try:
                loop = asyncio.get_event_loop()
                logger.debug(f"Event loop after {func_name}: {id(loop)}")
            except RuntimeError as e:
                logger.debug(f"No event loop after {func_name}: {e}")
            
            logger.debug(f"Exiting {func_name} in thread {thread_name} ({thread_id})")
            return result
        except Exception as e:
            logger.error(f"Error in {func_name}: {e}")
            raise
    
    return wrapper


def log_async_function_diagnostics(func):
    """Decorator to log async function entry/exit with event loop state."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        func_name = func.__qualname__
        thread_id = threading.get_ident()
        thread_name = threading.current_thread().name
        
        logger.debug(f"Entering async {func_name} in thread {thread_name} ({thread_id})")
        
        # Check event loop before
        try:
            loop = asyncio.get_event_loop()
            logger.debug(f"Event loop before async {func_name}: {id(loop)}")
        except RuntimeError as e:
            logger.debug(f"No event loop before async {func_name}: {e}")
        
        try:
            # Call the original function
            result = await func(*args, **kwargs)
            
            # Check event loop after
            try:
                loop = asyncio.get_event_loop()
                logger.debug(f"Event loop after async {func_name}: {id(loop)}")
            except RuntimeError as e:
                logger.debug(f"No event loop after async {func_name}: {e}")
            
            logger.debug(f"Exiting async {func_name} in thread {thread_name} ({thread_id})")
            return result
        except Exception as e:
            logger.error(f"Error in async {func_name}: {e}")
            raise
    
    return wrapper


def instrument_class(cls):
    """Instrument all methods of a class with diagnostic decorators."""
    for name, method in inspect.getmembers(cls, inspect.isfunction):
        if asyncio.iscoroutinefunction(method):
            setattr(cls, name, log_async_function_diagnostics(method))
        else:
            setattr(cls, name, log_function_diagnostics(method))
    return cls


def setup_diagnostic_hooks():
    """Set up all diagnostic hooks at once."""
    with MonkeyPatchEventLoop():
        logger.info("Event loop diagnostic hooks installed")
        inspect_event_loop("setup_diagnostic_hooks")
    
    return True


def debug_threads():
    """Print a diagnostic report of all threads and their event loops."""
    thread_info = get_thread_info()
    
    logger.info("=== THREAD DIAGNOSTICS ===")
    logger.info(f"Current thread: {thread_info['current_thread']['name']} ({thread_info['current_thread']['id']})")
    logger.info(f"Active threads: {len(thread_info['all_threads'])}")
    
    for thread_id, thread_name in thread_info['all_threads'].items():
        logger.info(f"  - Thread {thread_name} ({thread_id})")
    
    logger.info("Event loops by thread:")
    for thread_id, info in thread_info['thread_registry'].items():
        thread_name = info['name']
        loops = info['loops']
        logger.info(f"  - Thread {thread_name} ({thread_id}): {len(loops)} loops")
        for loop_id in loops:
            if loop_id in thread_info['event_loops']:
                loop_info = thread_info['event_loops'][loop_id]
                logger.info(f"    - Loop {loop_id} created at {loop_info['created_at']} by {loop_info['created_by']}")
    
    return thread_info


def install_event_loop_monitor():
    """Install a background thread to monitor event loops and report issues."""
    stop_event = threading.Event()
    
    def monitor_loop():
        """Background thread function to monitor event loops."""
        logger.info("Event loop monitor started")
        
        while not stop_event.is_set():
            try:
                # Check for event loop leaks
                current_loops = {}
                for thread_id, thread_info in _thread_registry.items():
                    for loop_id in thread_info['loops']:
                        if loop_id in _event_loop_registry:
                            loop_info = _event_loop_registry[loop_id]
                            if 'loop' in loop_info and not loop_info['loop'].is_closed():
                                if thread_id not in current_loops:
                                    current_loops[thread_id] = []
                                current_loops[thread_id].append(loop_id)
                
                # Report threads with multiple open event loops
                for thread_id, loops in current_loops.items():
                    if len(loops) > 1:
                        thread_name = _thread_registry[thread_id]['name']
                        logger.warning(
                            f"Thread {thread_name} ({thread_id}) has {len(loops)} open event loops: {loops}"
                        )
                
                # Check for event loops created in one thread but used in another
                for loop_id, info in _event_loop_registry.items():
                    if 'loop' in info and not info['loop'].is_closed():
                        creator_thread = info['thread_id']
                        for thread_id, thread_info in _thread_registry.items():
                            if thread_id != creator_thread and loop_id in thread_info['loops']:
                                logger.warning(
                                    f"Loop {loop_id} created in thread {info['thread_name']} ({creator_thread}) "
                                    f"is being used in thread {_thread_registry[thread_id]['name']} ({thread_id})"
                                )
            except Exception as e:
                logger.error(f"Error in event loop monitor: {e}")
            
            # Sleep for a bit
            stop_event.wait(5)
        
        logger.info("Event loop monitor stopped")
    
    # Start the monitor thread
    monitor_thread = threading.Thread(target=monitor_loop, name="EventLoopMonitor", daemon=True)
    monitor_thread.start()
    
    # Return the stop event so the caller can stop the monitor
    return stop_event


def cli_diagnostic_wrapper():
    """Function to directly add to a CLI command for event loop diagnostics.
    
    This function can be added to CLI commands to check event loop state at
    command execution time.
    
    Example:
    ```python
    @apify_config_group.command()
    def show():
        from scripts.event_loop_diagnostics import cli_diagnostic_wrapper
        cli_diagnostic_wrapper()  # Will check event loops before command runs
        
        # Rest of command logic
    ```
    """
    # Set up hooks if not already set up
    setup_diagnostic_hooks()
    
    # Print banner
    logger.info("*** CLI COMMAND DIAGNOSTIC WRAPPER ***")
    
    # Get command information
    frame = inspect.currentframe().f_back
    module = inspect.getmodule(frame).__name__
    lineno = frame.f_lineno
    code = frame.f_code.co_name
    
    logger.info(f"Command: {module}.{code}:{lineno}")
    
    # Check event loop state
    inspect_event_loop(f"cli_command_{code}")
    
    # Get thread info
    thread_info = debug_threads()
    
    # Check for event loop in current thread
    try:
        loop = asyncio.get_event_loop()
        logger.info(f"Current thread has event loop: {id(loop)}")
    except RuntimeError as e:
        logger.error(f"Current thread has NO event loop: {e}")
        
        # Create a new event loop and set it
        logger.info("Creating and setting new event loop...")
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        
        try:
            check_loop = asyncio.get_event_loop()
            logger.info(f"Successfully created new event loop: {id(check_loop)}")
        except RuntimeError as e2:
            logger.error(f"Still cannot get event loop after creating new one: {e2}")
    
    # Return diagnostic information
    return {
        'command': f"{module}.{code}:{lineno}",
        'event_loop_check': inspect_event_loop(f"cli_command_{code}_final"),
        'thread_info': thread_info
    }


# Example usage in main entrypoint
if __name__ == "__main__":
    setup_diagnostic_hooks()
    
    # Create and use an event loop
    try:
        loop = asyncio.get_event_loop()
        logger.info(f"Got event loop: {id(loop)}")
    except RuntimeError:
        logger.info("Creating new event loop")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # Check event loop state
    inspect_event_loop("main")
    
    # Create a background thread that tries to use an event loop
    def thread_func():
        try:
            loop = asyncio.get_event_loop()
            logger.info(f"Thread got event loop: {id(loop)}")
        except RuntimeError as e:
            logger.error(f"Thread failed to get event loop: {e}")
            
            # Create a new event loop in the thread
            logger.info("Thread creating new event loop")
            thread_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(thread_loop)
            
            logger.info(f"Thread created and set event loop: {id(thread_loop)}")
    
    # Start a thread
    t = threading.Thread(target=thread_func)
    t.start()
    t.join()
    
    # Check event loop state again
    inspect_event_loop("after_thread")
    
    # Show all thread info
    debug_threads()
    
    logger.info("Diagnostic script completed")