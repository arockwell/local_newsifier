import asyncio
import functools
from typing import Generator

import pytest


@pytest.fixture(scope="function")
def isolated_event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an isolated event loop for each test."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    pending = asyncio.all_tasks(loop)
    for task in pending:
        task.cancel()
    if pending:
        loop.run_until_complete(asyncio.wait(pending, timeout=0.1))
    loop.close()


@pytest.fixture(scope="function")
async def async_test_db():
    """Create isolated test database with async interface."""
    from local_newsifier.database.async_engine import AsyncDatabase
    from sqlmodel import SQLModel

    db = AsyncDatabase("sqlite+aiosqlite:///:memory:")
    await db.initialize()
    await db.run_sync(lambda engine: SQLModel.metadata.create_all(engine))
    yield db
    await db.run_sync(lambda engine: SQLModel.metadata.drop_all(engine))
    await db.dispose()


@pytest.fixture(scope="function")
async def async_session(async_test_db):
    """Get async session for testing."""
    async with async_test_db.get_session() as session:
        yield session


async def run_async_test(test_func, *args, **kwargs):
    """Run an async test function and return result."""
    return await test_func(*args, **kwargs)


def sync_run(async_func, *args, **kwargs):
    """Run an async function from synchronous test."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(async_func(*args, **kwargs))


class AsyncMockSession:
    """Mock async session for testing."""

    def __init__(self, mock_results=None):
        self.mock_results = mock_results or {}
        self.committed = False
        self.rolled_back = False
        self.closed = False

    async def fetch_all(self, query):
        query_str = str(query)
        return self.mock_results.get(query_str, [])

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.rolled_back = True

    async def close(self):
        self.closed = True


def async_test(func):
    """Decorator to run a test using the isolated event loop."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        loop = next((arg for arg in args if isinstance(arg, asyncio.AbstractEventLoop)), None)
        if loop is None:
            pytest.fail("async_test requires isolated_event_loop fixture")
        return loop.run_until_complete(func(*args, **kwargs))

    return wrapper
