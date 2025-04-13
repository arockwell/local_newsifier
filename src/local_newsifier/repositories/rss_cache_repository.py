"""Repository for handling RSS feed cache in the database."""

from datetime import datetime, timezone, timedelta
from typing import List, Set

from sqlalchemy.orm import Session

from ..models.database import ProcessedURLDB


class RSSCacheRepository:
    """Repository for managing RSS feed cache in the database."""

    def __init__(self, session: Session):
        """
        Initialize the repository.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session

    def add_processed_url(self, url: str, feed_url: str) -> None:
        """
        Add a processed URL to the cache.

        Args:
            url: URL that was processed
            feed_url: Source feed URL
        """
        processed_url = ProcessedURLDB(url=url, feed_url=feed_url)
        self.session.add(processed_url)
        self.session.commit()

    def is_processed(self, url: str) -> bool:
        """
        Check if a URL has been processed.

        Args:
            url: URL to check

        Returns:
            True if URL has been processed, False otherwise
        """
        return self.session.query(ProcessedURLDB).filter_by(url=url).first() is not None

    def get_processed_urls(self, feed_url: str) -> Set[str]:
        """
        Get all processed URLs for a feed.

        Args:
            feed_url: Feed URL to get processed URLs for

        Returns:
            Set of processed URLs
        """
        urls = self.session.query(ProcessedURLDB.url).filter_by(feed_url=feed_url).all()
        return {url[0] for url in urls}

    def get_new_urls(self, urls: List[str], feed_url: str) -> List[str]:
        """
        Get URLs that haven't been processed yet.

        Args:
            urls: List of URLs to check
            feed_url: Source feed URL

        Returns:
            List of new URLs
        """
        processed_urls = self.get_processed_urls(feed_url)
        return [url for url in urls if url not in processed_urls]

    def cleanup_old_urls(self, days: int = 30) -> None:
        """
        Remove URLs processed more than specified days ago.

        Args:
            days: Number of days to keep URLs
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        self.session.query(ProcessedURLDB).filter(
            ProcessedURLDB.processed_at < cutoff
        ).delete()
        self.session.commit() 