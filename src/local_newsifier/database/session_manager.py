"""Improved database session management."""

from contextlib import contextmanager
from typing import Generator, Optional

from sqlmodel import Session, create_engine, SQLModel

from local_newsifier.config.settings import get_settings


class SessionManager:
    """SessionManager provides consistent session handling for the application."""

    def __init__(self, url: Optional[str] = None):
        """Initialize the session manager with a database URL.

        Args:
            url: Database URL (if None, uses settings)
        """
        self._engine = None
        self._url = url

    @property
    def engine(self):
        """Lazy-loaded SQLModel engine.

        Returns:
            SQLModel engine
        """
        if self._engine is None:
            self._create_engine()
        return self._engine

    def _create_engine(self):
        """Create and configure the database engine."""
        settings = get_settings()
        url = self._url or str(settings.DATABASE_URL)

        # Only add application_name for PostgreSQL
        connect_args = {}
        if url.startswith("postgresql:"):
            connect_args = {"application_name": "local_newsifier"}

        self._engine = create_engine(
            url,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            connect_args=connect_args,
            echo=settings.DB_ECHO,
        )

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Get a database session with transaction management.

        Yields:
            Database session
        """
        session = Session(self.engine)
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_db_and_tables(self):
        """Create all tables in the database."""
        SQLModel.metadata.create_all(self.engine)


# Global instance for application-wide use
default_session_manager = SessionManager()


def get_session_manager() -> SessionManager:
    """Get the default session manager.

    Returns:
        Default session manager instance
    """
    return default_session_manager
