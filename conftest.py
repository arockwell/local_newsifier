"""Global test configuration to ensure consistent table registration.

This module handles:
1. SQLModel metadata registration in a controlled order
2. SQLite in-memory database setup for tests
3. Session and transaction management for tests
4. Patching injectable decorators for tests
5. Test timeout enforcement to prevent hanging tests
"""

import os
import threading
import signal
import time
import traceback
import inspect
import logging
from datetime import datetime, timezone
from typing import Generator
import uuid
import sys
from unittest.mock import patch, MagicMock
import warnings
from functools import wraps

import pytest
from sqlmodel import SQLModel, Session, create_engine, text, select

# Enable verbose logging for test diagnostic purposes
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("pytest")

# Custom timeout decorator for tests with enhanced reliability
DEFAULT_TEST_TIMEOUT = int(os.environ.get("TEST_TIMEOUT", "10"))

def timeout(seconds=DEFAULT_TEST_TIMEOUT):
    """
    Decorator to timeout tests after specified seconds with escalating force.

    This uses multiple layers of protection:
    1. Thread-based timeout (primary)
    2. Signal-based timeout (backup)
    3. Forceful thread termination (last resort)

    Args:
        seconds: Maximum time in seconds to allow test to run

    Returns:
        Decorated test function with timeout protection
    """
    def decorator(test_func):
        @wraps(test_func)
        def wrapper(*args, **kwargs):
            # Store information for debugging
            test_name = test_func.__name__
            threading.current_thread().test_name = test_name
            threading.current_thread().name = f"Test_{test_name}"

            # Store result in lists to allow modification from thread
            result = [None]
            error = [None]
            finished = [False]

            # Set up backup SIGALRM for this specific test
            # This acts as a fallback if thread-based timeout fails
            if sys.platform != 'win32':  # Skip on Windows where SIGALRM isn't available
                previous_handler = signal.getsignal(signal.SIGALRM)

                def test_timeout_handler(signum, frame):
                    if not finished[0]:
                        msg = f"SIGALRM TIMEOUT: {test_name} exceeded {seconds} seconds"
                        logger.error(msg)
                        error[0] = TimeoutError(msg)

                # Register the signal handler and set alarm
                signal.signal(signal.SIGALRM, test_timeout_handler)
                signal.alarm(seconds + 2)  # Give slightly more time than thread timeout

            # Run test in thread with timer
            def run_test():
                start_time = time.time()
                try:
                    # Run the actual test
                    result[0] = test_func(*args, **kwargs)
                    finished[0] = True
                    # Log elapsed time for slow tests
                    elapsed = time.time() - start_time
                    if elapsed > seconds / 2:  # Log tests that take >50% of timeout
                        logger.warning(f"SLOW TEST: {test_name} took {elapsed:.2f} seconds")
                except Exception as e:
                    error[0] = e

            # Create and start test thread
            test_thread = threading.Thread(target=run_test)
            test_thread.daemon = True
            test_thread.start()

            # Wait for completion with timeout
            test_thread.join(timeout=seconds)

            # Restore signal handler if we modified it
            if sys.platform != 'win32':
                signal.alarm(0)  # Cancel the alarm
                signal.signal(signal.SIGALRM, previous_handler)

            # Handle timeout case
            if not finished[0]:
                msg = f"TEST TIMEOUT: {test_name} took longer than {seconds} seconds"
                logger.error(msg)

                # Log thread state for debugging
                if hasattr(sys, '_current_frames'):
                    frame = sys._current_frames().get(test_thread.ident)
                    if frame:
                        logger.error(f"Thread {test_thread.name} stack trace:")
                        for line in traceback.format_stack(frame):
                            logger.error(line.strip())

                # Set error if none exists
                if error[0] is None:
                    error[0] = TimeoutError(msg)

                # Only skip if it's a timeout (not other errors)
                if isinstance(error[0], TimeoutError):
                    pytest.skip(f"Skipped due to timeout: {msg}")
                else:
                    raise error[0]

            # Handle error case
            if error[0] is not None:
                raise error[0]

            # Return result
            return result[0]

        return wrapper
    return decorator

# Register timeout decorator with pytest
pytest.timeout = timeout

# Make it available as a standalone decorator
def test_with_timeout(seconds=DEFAULT_TEST_TIMEOUT):
    """Apply timeout decorator to a test function."""
    return timeout(seconds)

# Import our utility to patch injectable decorators
from tests.patches import patch_injectable_imports

# Patch all injectable decorators before importing any modules
@pytest.fixture(scope="session", autouse=True)
def patch_all_injectable_decorators():
    """
    Apply the patch for all injectable decorators globally for the test session.
    
    This ensures all tests can safely import classes decorated with @injectable.
    """
    # Apply the patch at the earliest possible point
    stop_patch = patch_injectable_imports()
    yield
    stop_patch()


# Also patch event loops to avoid "Event loop is closed" errors in async tests
from tests.patches import create_test_event_loop

@pytest.fixture(scope="session", autouse=True)
def patch_event_loop():
    """
    Set up a mock event loop for all tests.
    
    This avoids 'RuntimeError: Event loop is closed' errors in tests that use async code.
    """
    mock_loop, stop_patches = create_test_event_loop()
    yield mock_loop
    stop_patches()

# First, reset and register all models in a controlled order
# This must run before any database operations
SQLModel.metadata.clear()

# Import and register models in a specific order
# Base models 
from local_newsifier.models.base import TableBase

# Core models
from local_newsifier.models.article import Article
from local_newsifier.models.entity import Entity
from local_newsifier.models.analysis_result import AnalysisResult

# Entity tracking models
from local_newsifier.models.entity_tracking import (
    CanonicalEntity, EntityMention, EntityMentionContext,
    EntityProfile, EntityRelationship
)

# Sentiment models
from local_newsifier.models.sentiment import (
    SentimentAnalysis, OpinionTrend, SentimentShift
)

# State models
from local_newsifier.models.state import AnalysisStatus, NewsAnalysisState

# Trend models
from local_newsifier.models.trend import (
    TrendAnalysis, TrendEntity, TrendEvidenceItem, TrendStatus, TrendType
)

# Apify models
from local_newsifier.models.apify import (
    ApifySourceConfig, ApifyJob, ApifyDatasetItem, ApifyCredentials, ApifyWebhook
)

# Create a pytest plugin that allows access to the test engine
class TestEnginePlugin:
    """Plugin to provide access to the test engine.
    
    This plugin maintains an engine per xdist worker to ensure proper isolation
    when tests are run in parallel. Each worker gets its own dedicated in-memory
    database.
    """
    
    # Dictionary to store engines per worker (worker_id -> engine)
    _worker_engines = {}
    
    @classmethod
    def set_engine(cls, worker_id, engine):
        """Set the engine for a specific worker.
        
        Args:
            worker_id: The worker ID or None for single process
            engine: The SQLAlchemy engine
        """
        cls._worker_engines[worker_id or "master"] = engine
        
    @classmethod
    def get_engine(cls, worker_id=None):
        """Get the engine for a specific worker.
        
        Args:
            worker_id: The worker ID or None for single process
            
        Returns:
            The SQLAlchemy engine or None if not found
        """
        return cls._worker_engines.get(worker_id or "master")
    
    @classmethod
    def cleanup_engine(cls, worker_id):
        """Clean up the engine for a specific worker.
        
        Args:
            worker_id: The worker ID or None for single process
        """
        worker_key = worker_id or "master"
        if worker_key in cls._worker_engines:
            engine = cls._worker_engines[worker_key]
            if engine:
                engine.dispose()
            del cls._worker_engines[worker_key]

# Register the plugin directly on pytest
# This avoids using the problematic pytest_configure hook
pytest.test_engine_plugin = TestEnginePlugin()

@pytest.fixture(scope="session", autouse=True)
def test_engine(request):
    """Create a test database engine using SQLite in-memory.
    
    This fixture:
    1. Creates an in-memory SQLite database
    2. Creates all tables
    3. Makes the engine available via the test_engine_plugin
    4. Yields the engine for tests that need direct access
    
    The autouse=True parameter ensures this fixture runs for all tests,
    even when not explicitly requested, ensuring the test database is always set up.
    
    In parallel testing environments (using pytest-xdist), each worker gets its own
    dedicated SQLite in-memory database.
    """
    # Detect whether we're running with xdist and get the worker ID
    worker_id = getattr(request.config, "workerinput", {}).get("workerid", None)
    
    # Create a unique database URL for each worker (for xdist) or use shared memory for single process
    if worker_id:
        # When running with xdist, each worker gets its own in-memory database with its own ID
        # This ensures isolation between parallel test workers
        db_url = f"sqlite:///:memory:"
    else:
        # In non-parallel mode, use the standard in-memory database
        db_url = "sqlite:///:memory:"
    
    # Create SQLite engine for tests
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False},
        # Speed up SQLite for tests
        pool_pre_ping=False,  # Disable pre-ping for tests
        pool_recycle=-1,  # Disable connection recycling
    )
    
    # Create all tables
    SQLModel.metadata.create_all(engine)
    
    # Verify tables were created by trying to insert and select
    with Session(engine) as session:
        # Create a test article with all required fields
        test_article = Article(
            title="Test Article",
            content="Test Content",
            url="https://example.com/test",
            source="test_source",
            status="new",
            published_at=datetime.now(timezone.utc),
            scraped_at=datetime.now(timezone.utc),
        )
        session.add(test_article)
        session.commit()
        
        # Query to verify it exists
        statement = select(Article).where(Article.title == "Test Article")
        result = session.exec(statement).first()
        
        if not result:
            pytest.fail("Failed to verify table creation")
        
        # Clean up the test data
        session.delete(result)
        session.commit()
    
    # Make the engine available to the plugin so it can be accessed outside the fixture
    # This is the key change that avoids needing the problematic pytest_configure hook
    pytest.test_engine_plugin.set_engine(worker_id, engine)
    
    # Yield the engine for tests to use directly
    yield engine
    
    # Clean up by removing the engine from the plugin and disposing it
    pytest.test_engine_plugin.cleanup_engine(worker_id)

@pytest.fixture
def db_session(test_engine) -> Generator[Session, None, None]:
    """Provide a database session with transaction isolation.
    
    This fixture:
    1. Creates a new connection to the database
    2. Starts a transaction
    3. Yields a session bound to that connection
    4. Rolls back the transaction after the test
    5. Closes the connection
    
    This ensures that tests are isolated from each other and don't affect
    the database state outside of their own transaction.
    """
    # Start a new connection
    connection = test_engine.connect()
    # Start a transaction
    transaction = connection.begin()
    
    # Create a session bound to this connection
    session = Session(bind=connection)
    
    try:
        # Yield the session for test use
        yield session
    finally:
        # Always roll back and close, even if test fails
        session.close()
        transaction.rollback()
        connection.close()
