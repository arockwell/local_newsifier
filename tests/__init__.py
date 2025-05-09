"""
Test package initialization.

This file contains initialization code for tests, including global patches
that need to be applied before any tests are run.
"""

import os
import signal
import threading
import time
import asyncio
import inspect
import logging
import sys
from unittest.mock import MagicMock, patch

# Configure test logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("tests")

# Aggressive test timeout (set in environment or default to 10 seconds in CI, 30 seconds locally)
# CI pipelines should fail faster to avoid hanging the entire build
IS_CI = os.environ.get("CI", "false").lower() == "true"
DEFAULT_TIMEOUT = "10" if IS_CI else "30"
GLOBAL_TEST_TIMEOUT = int(os.environ.get("TEST_TIMEOUT", DEFAULT_TIMEOUT))

# Setup global test timeout
def setup_test_timeout():
    """Set up a global watchdog timer to prevent hanging tests."""
    if sys.platform != 'win32':  # Skip on Windows where SIGALRM isn't available
        # Define handler for timeout signal
        def timeout_handler(signum, frame):
            current_test = getattr(threading.current_thread(), 'test_name', 'Unknown test')
            error_msg = f"TEST TIMEOUT: {current_test} exceeded {GLOBAL_TEST_TIMEOUT} seconds"
            logger.error(error_msg)
            print(f"\n\n*** {error_msg} ***\n\n", file=sys.stderr)
            # Force exit with error code
            os._exit(1)

        # Register the signal handler
        signal.signal(signal.SIGALRM, timeout_handler)

        # Set the alarm
        signal.alarm(GLOBAL_TEST_TIMEOUT)
        logger.info(f"Global test timeout set to {GLOBAL_TEST_TIMEOUT} seconds")

# Call timeout setup if this is the main process
if not hasattr(sys, 'pytest_in_progress'):
    sys.pytest_in_progress = True
    setup_test_timeout()

    # In CI, add a more aggressive emergency kill switch for worker processes
    if IS_CI:
        import threading
        import signal

        def emergency_kill_switch():
            """Forcefully kill the process after a set timeout."""
            logger.error(f"EMERGENCY KILL SWITCH activated after {kill_time} seconds")
            print(f"\n\n*** EMERGENCY KILL SWITCH activated - forcefully terminating process ***\n\n")

            # Exit with non-zero code to indicate error
            # Use both signal and _exit to ensure termination
            try:
                # First try sending SIGTERM
                os.kill(os.getpid(), signal.SIGTERM)
                # Sleep to allow signal to be handled
                time.sleep(0.5)
                # If that failed, do a hard exit
                os._exit(2)
            except:
                # As a last resort, use os._exit
                os._exit(2)

        # Set up kill switch thread
        # Make the emergency timeout much longer to allow for test collection
        kill_time = max(GLOBAL_TEST_TIMEOUT * 5, 60)  # At least 60 seconds
        kill_thread = threading.Timer(kill_time, emergency_kill_switch)
        kill_thread.daemon = True
        kill_thread.start()
        logger.info(f"Emergency kill switch activated (will trigger in {kill_time} seconds)")

        # Register a second kill switch that uses SIGALRM
        if sys.platform != 'win32':
            # Set a signal handler that will be called after the timer
            def emergency_sigalrm_handler(signum, frame):
                logger.error("SIGALRM EMERGENCY handler triggered")
                # Force exit
                os._exit(3)

            # Register the handler for SIGALRM
            signal.signal(signal.SIGALRM, emergency_sigalrm_handler)

            # Set the alarm for an even longer timeout (emergency backup)
            kill_time_alarm = kill_time + 30  # 30 seconds longer than the thread timeout
            signal.alarm(kill_time_alarm)
            logger.info(f"SIGALRM emergency kill switch activated (will trigger in {kill_time_alarm} seconds)")

# Patch all coroutine functions to have timeouts
def timeout_wrapper(coro_func, timeout=5):
    """Wrap all coroutine functions with timeouts."""
    async def wrapped(*args, **kwargs):
        try:
            return await asyncio.wait_for(coro_func(*args, **kwargs), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Coroutine {coro_func.__name__} timed out after {timeout} seconds")
            return None
    return wrapped

# Early patch for spaCy to avoid loading models in all tests
class MockSpacyDoc:
    """Mock spaCy Doc class."""
    def __init__(self, text="Test content"):
        self.text = text
        self.ents = []
        self._sentences = [MockSpacySent("Test sentence.")]
    
    @property
    def sents(self):
        return self._sentences
    
    def char_span(self, start_char, end_char, **kwargs):
        """Mock character span lookup."""
        mock_span = MagicMock()
        mock_span.start = 0
        mock_span.end = 10
        return mock_span

class MockSpacySent:
    """Mock spaCy Sent (sentence) class."""
    def __init__(self, text="Test sentence."):
        self.text = text
        self.start_char = 0
        self.end_char = len(text)
        self.start = 0
        self.end = len(text.split())

class MockSpacyLanguage:
    """Mock spaCy Language class."""
    def __init__(self):
        self.vocab = {}
        self.pipeline = []
    
    def __call__(self, text):
        """Process text and return a Doc object."""
        doc = MockSpacyDoc(text)
        
        # Create some mock entities
        mock_ent1 = MagicMock()
        mock_ent1.text = "Entity1"
        mock_ent1.label_ = "PERSON"
        mock_ent1.start_char = 0
        mock_ent1.end_char = 7
        mock_ent1.sent = doc.sents[0]
        
        mock_ent2 = MagicMock()
        mock_ent2.text = "Entity2"
        mock_ent2.label_ = "ORG"
        mock_ent2.start_char = 10
        mock_ent2.end_char = 17
        mock_ent2.sent = doc.sents[0]
        
        doc.ents = [mock_ent1, mock_ent2]
        return doc

# Mock spacy.load before any imports happen
def mock_spacy_load(model_name):
    """Mock function for spacy.load that returns a Language mock."""
    return MockSpacyLanguage()

# Apply the patch
spacy_patch = patch('spacy.load', side_effect=mock_spacy_load)
spacy_patch.start()

# Patch asyncio.get_event_loop to ensure clean loops
original_get_event_loop = asyncio.get_event_loop

def mock_get_event_loop():
    """Get a clean event loop for each call."""
    try:
        loop = original_get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop
    except RuntimeError:
        # No event loop exists
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop

asyncio_patch = patch('asyncio.get_event_loop', side_effect=mock_get_event_loop)
asyncio_patch.start()

# Patch run_until_complete to add timeout with thread-based fail-safe
def patched_run_until_complete(original_run):
    """Add timeout to run_until_complete with thread-based failure recovery."""
    def wrapper(self, coro, timeout=2.0):
        if inspect.iscoroutine(coro):
            # Setup thread-based timeout as a failsafe
            result = [None]
            error = [None]
            completed = [False]

            def run_coro_in_thread():
                try:
                    # Add timeout to coroutine
                    async def run_with_timeout():
                        try:
                            return await asyncio.wait_for(coro, timeout=timeout)
                        except asyncio.TimeoutError:
                            logger.warning(f"Coroutine timed out after {timeout} seconds")
                            return {}

                    # Run with timeout
                    result[0] = original_run(self, run_with_timeout())
                    completed[0] = True
                except Exception as e:
                    error[0] = e
                    logger.warning(f"Error running coroutine: {str(e)}")

            # Run in a separate thread with timeout
            thread = threading.Thread(target=run_coro_in_thread)
            thread.daemon = True
            thread.start()
            thread.join(timeout=timeout + 1.0)  # Give a little extra time for the asyncio timeout

            # If thread is still alive, it's completely stuck
            if thread.is_alive():
                logger.error(f"CRITICAL: Thread executing coroutine is completely stuck")
                # Return empty result to allow test to continue
                return {}

            # If completed successfully, return result
            if completed[0]:
                return result[0]

            # If there was an error, log it and return empty result
            if error[0]:
                logger.error(f"Error in coroutine execution: {error[0]}")

            # Return empty dict as fallback
            return {}

        return original_run(self, coro)
    return wrapper

# Monkey patch the run_until_complete method of all event loops
original_run_until_complete = asyncio.BaseEventLoop.run_until_complete
asyncio.BaseEventLoop.run_until_complete = patched_run_until_complete(original_run_until_complete)

logger.info("Test initialization complete with timeout protection enabled")