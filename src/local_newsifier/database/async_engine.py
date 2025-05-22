import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Any, Callable, Optional

from sqlmodel import Session

from local_newsifier.database.engine import get_engine


class AsyncDatabase:
    """Asynchronous wrapper around the synchronous SQLModel engine."""

    def __init__(self, database_url: Optional[str] = None, max_workers: Optional[int] = None):
        self.database_url = database_url
        self.executor = ThreadPoolExecutor(max_workers=max_workers or 10)
        self._engine = None

    def _initialize_engine(self) -> None:
        """Initialize the underlying synchronous engine."""
        if (
            self.database_url
            and self.database_url.startswith("sqlite")
            and ":memory:" in self.database_url
        ):
            from sqlalchemy.pool import StaticPool
            from sqlmodel import create_engine

            self._engine = create_engine(
                self.database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
        else:
            self._engine = get_engine(self.database_url, test_mode=True)

    async def initialize(self) -> None:
        """Asynchronously initialize the database engine."""
        await self.run_sync(self._initialize_engine)

    async def dispose(self) -> None:
        """Dispose the engine and shutdown the executor."""
        if self._engine is not None:
            await self.run_sync(self._engine.dispose)
        self.executor.shutdown(wait=True)

    async def run_sync(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """Run a synchronous function in a background thread."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            partial(func, *args, **kwargs)
        )

    def get_session(self) -> "AsyncSession":
        """Return an asynchronous session context manager."""
        return AsyncSession(self)


class AsyncSession:
    """Async context manager for SQLModel Session."""

    def __init__(self, db: AsyncDatabase):
        self.db = db
        self.session: Optional[Session] = None

    async def __aenter__(self) -> "AsyncSession":
        self.session = await self.db.run_sync(lambda: Session(self.db._engine))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            await self.async_rollback()
        await self.close()

    async def async_execute_query(self, query: Any) -> Any:
        return await self.db.run_sync(lambda q=query: self.session.exec(q))

    async def async_fetch_one(self, query: Any) -> Any:
        return await self.db.run_sync(lambda q=query: self.session.exec(q).one())

    async def async_fetch_all(self, query: Any) -> Any:
        return await self.db.run_sync(lambda q=query: self.session.exec(q).all())

    async def async_commit(self) -> None:
        await self.db.run_sync(self.session.commit)

    async def async_rollback(self) -> None:
        await self.db.run_sync(self.session.rollback)

    async def commit(self) -> None:
        await self.async_commit()

    async def rollback(self) -> None:
        await self.async_rollback()

    async def close(self) -> None:
        if self.session is not None:
            await self.db.run_sync(self.session.close)


_async_db: Optional[AsyncDatabase] = None


async def get_async_database() -> AsyncDatabase:
    """Return a global AsyncDatabase instance."""
    global _async_db
    if _async_db is None:
        _async_db = AsyncDatabase()
        await _async_db.initialize()
    return _async_db
