"""Async provider functions for dependency injection.

This module contains async provider functions for components that require
async database sessions and operations.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from local_newsifier.database.async_engine import get_async_session


async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session.

    This is a direct passthrough to the async engine's get_async_session
    function, provided here for consistency with the DI pattern.

    Yields:
        AsyncSession: Async database session
    """
    async for session in get_async_session():
        yield session
