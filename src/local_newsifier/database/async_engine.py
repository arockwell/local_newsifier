import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Callable, Any

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel


class AsyncDatabase:
    """Minimal asynchronous database wrapper for tests."""

    def __init__(self, url: str):
        self._engine = create_async_engine(url, echo=False, future=True)
        self._sessionmaker = sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False
        )

    async def initialize(self) -> None:
        """Initialize the database (no-op for SQLite)."""
        # For SQLite memory DB nothing extra is required
        pass

    async def run_sync(self, func: Callable[[Any], Any]) -> Any:
        """Run a synchronous function in an async engine context."""
        async with self._engine.begin() as conn:
            return await conn.run_sync(func)

    async def dispose(self) -> None:
        await self._engine.dispose()

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Provide an async session context manager."""
        async with self._sessionmaker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


