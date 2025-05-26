"""Async database engine and session management using SQLModel and SQLAlchemy."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from local_newsifier.config.settings import get_settings

logger = logging.getLogger(__name__)


class AsyncDatabaseManager:
    """Manages async database connections and sessions."""

    def __init__(self, database_url: Optional[str] = None):
        """Initialize the async database manager.

        Args:
            database_url: Optional database URL override
        """
        self._engine = None
        self._sessionmaker = None
        self._database_url = database_url

    @property
    def database_url(self) -> str:
        """Get the async database URL."""
        if self._database_url:
            return self._database_url

        settings = get_settings()
        sync_url = str(settings.DATABASE_URL)

        # Convert sync PostgreSQL URL to async
        if sync_url.startswith("postgresql://"):
            return sync_url.replace("postgresql://", "postgresql+asyncpg://")
        elif sync_url.startswith("postgresql+psycopg2://"):
            return sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")
        else:
            raise ValueError(f"Unsupported database URL scheme: {sync_url}")

    def get_engine(self):
        """Get or create the async engine."""
        if not self._engine:
            settings = get_settings()
            self._engine = create_async_engine(
                self.database_url,
                echo=getattr(settings, "DB_ECHO", False),
                pool_size=getattr(settings, "DB_POOL_SIZE", 5),
                max_overflow=getattr(settings, "DB_MAX_OVERFLOW", 10),
                pool_pre_ping=True,
                pool_recycle=300,  # Recycle connections after 5 minutes
            )
            logger.info("Async database engine created")
        return self._engine

    def get_sessionmaker(self):
        """Get or create the async session maker."""
        if not self._sessionmaker:
            self._sessionmaker = async_sessionmaker(
                self.get_engine(), class_=AsyncSession, expire_on_commit=False
            )
        return self._sessionmaker

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an async database session.

        Yields:
            AsyncSession: Async database session
        """
        async with self.get_sessionmaker()() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def create_all_tables(self):
        """Create all database tables asynchronously."""
        async with self.get_engine().begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
            logger.info("All database tables created")

    async def close(self):
        """Close the database engine."""
        if self._engine:
            await self._engine.dispose()
            logger.info("Async database engine closed")


# Global instance for easy access
_async_db_manager = None


def get_async_db_manager() -> AsyncDatabaseManager:
    """Get the global async database manager instance."""
    global _async_db_manager
    if not _async_db_manager:
        _async_db_manager = AsyncDatabaseManager()
    return _async_db_manager


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting an async database session.

    Yields:
        AsyncSession: Async database session
    """
    manager = get_async_db_manager()
    async with manager.get_session() as session:
        yield session
