"""News pipeline service for coordinating the entire news processing pipeline."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from local_newsifier.errors import handle_database, handle_web_scraper
from local_newsifier.services.article_service import ArticleService


class NewsPipelineService:
    """Service for coordinating the entire news processing pipeline."""

    def __init__(self, article_service, web_scraper, file_writer=None, session_factory=None):
        """Initialize with dependencies.

        Args:
            article_service: Service for article operations
            web_scraper: Tool for scraping web content
            file_writer: Optional tool for writing results to files
            session_factory: Factory for database sessions
        """
        self.article_service = article_service
        self.web_scraper = web_scraper
        self.file_writer = file_writer
        self.session_factory = session_factory

    @handle_web_scraper
    @handle_database
    def process_url(self, url: str) -> Dict[str, Any]:
        """Process a news article from a URL.

        Args:
            url: URL of the article to process

        Returns:
            Dictionary with processing results
        """
        # Scrape content
        scraped_data = self.web_scraper.scrape_url(url)

        if not scraped_data:
            return {"status": "error", "message": "Failed to scrape content"}

        try:
            # Process article
            result = self.article_service.process_article(
                url=url,
                content=scraped_data["content"],
                title=scraped_data["title"],
                published_at=scraped_data.get("published_at", datetime.now()),
            )

            # Save results to file if needed
            if self.file_writer:
                try:
                    file_path = self.file_writer.write_results(result)
                    result["file_path"] = file_path
                except Exception as e:
                    # Handle file writer errors
                    result["error"] = f"Error writing results to file: {str(e)}"

            return result
        except Exception as e:
            # Handle processing errors
            return {"status": "error", "message": f"Error processing article: {str(e)}", "url": url}

    @handle_database
    def process_content(
        self, url: str, content: str, title: str, published_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Process article content directly.

        Args:
            url: URL of the article
            content: Article content
            title: Article title
            published_at: Optional publication date

        Returns:
            Dictionary with processing results
        """
        # Use current time if no publication date provided
        if published_at is None:
            published_at = datetime.now()

        try:
            # Process article
            result = self.article_service.process_article(
                url=url, content=content, title=title, published_at=published_at
            )

            # Save results to file if needed
            if self.file_writer:
                try:
                    file_path = self.file_writer.write_results(result)
                    result["file_path"] = file_path
                except Exception as e:
                    # Handle file writer errors
                    result["error"] = f"Error writing results to file: {str(e)}"

            return result
        except Exception as e:
            # Handle processing errors
            return {"status": "error", "message": f"Error processing article: {str(e)}", "url": url}
