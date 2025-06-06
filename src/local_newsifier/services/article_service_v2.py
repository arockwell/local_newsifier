"""Article service using the new database_operation context manager.

This is an example of how to migrate from @handle_database decorator
to the unified database_operation context manager.
"""

from datetime import datetime
from typing import Any, Callable, Dict, Optional

from fastapi_injectable import injectable

from local_newsifier.database import database_operation
from local_newsifier.models.analysis_result import AnalysisResult
from local_newsifier.models.article import Article
from local_newsifier.utils.dates import parse_date_safe
from local_newsifier.utils.url import extract_source_from_url


@injectable(use_cache=False)
class ArticleServiceV2:
    """Service for article-related operations using unified error handling."""

    def __init__(
        self,
        article_crud,
        analysis_result_crud,
        entity_service,
        session_factory: Callable,
    ):
        """Initialize with dependencies."""
        self.article_crud = article_crud
        self.analysis_result_crud = analysis_result_crud
        self.entity_service = entity_service
        self.session_factory = session_factory

    def process_article(
        self, url: str, content: str, title: str, published_at: datetime
    ) -> Dict[str, Any]:
        """Process an article including entity extraction and tracking.

        Uses the new database_operation context manager instead of @handle_database.
        """
        with self.session_factory() as session:
            # Use context manager for database operations
            with database_operation(session, "process article"):
                # Extract domain as source
                source = extract_source_from_url(url)

                # Create article record
                article_data = Article(
                    url=url,
                    title=title,
                    content=content,
                    published_at=published_at,
                    status="analyzed",
                    source=source,
                    scraped_at=datetime.now(),
                )
                article = self.article_crud.create(session, obj_in=article_data)

            # Process entities (might have its own error handling)
            entities = self.entity_service.process_article_entities(
                article_id=article.id, content=content, title=title, published_at=published_at
            )

            # Create analysis result
            with database_operation(session, "create analysis result"):
                entity_types = set(entity.get("canonical_type", "UNKNOWN") for entity in entities)
                entity_counts = {
                    entity_type: len(
                        [e for e in entities if e.get("canonical_type", "UNKNOWN") == entity_type]
                    )
                    for entity_type in entity_types
                }

                analysis_result_data = {
                    "entities": entities,
                    "statistics": {"entity_counts": entity_counts, "total_entities": len(entities)},
                }

                analysis_result_obj = AnalysisResult(
                    article_id=article.id,
                    analysis_type="entity_analysis",
                    results=analysis_result_data,
                )

                self.analysis_result_crud.create(session, obj_in=analysis_result_obj)

                # Commit the transaction
                session.commit()

            return {
                "article_id": article.id,
                "title": article.title,
                "url": article.url,
                "entities": entities,
                "analysis_result": analysis_result_data,
            }

    def get_article(self, article_id: int) -> Optional[Dict[str, Any]]:
        """Get article data by ID using context manager."""
        with self.session_factory() as session:
            with database_operation(session, f"get article {article_id}"):
                article = self.article_crud.get(session, id=article_id)

                if not article:
                    return None

                # Get analysis results
                analysis_results = self.analysis_result_crud.get_by_article(
                    session, article_id=article_id
                )

                return {
                    "article_id": article.id,
                    "title": article.title,
                    "url": article.url,
                    "content": article.content,
                    "published_at": article.published_at,
                    "status": article.status,
                    "analysis_results": [result.results for result in analysis_results],
                }

    def create_article_from_rss_entry(self, entry: Dict[str, Any]) -> Optional[int]:
        """Create a new article from an RSS feed entry."""
        # Extract data from the RSS entry
        title = entry.get("title", "Untitled")
        url = entry.get("link", "")

        # Extract source using utility
        source = entry.get("source", {}).get("title", "")
        if not source and "feed_url" in entry:
            source = extract_source_from_url(entry.get("feed_url", ""))
        if not source and url:
            source = extract_source_from_url(url)

        # Handle published date parsing using utility
        published_at = parse_date_safe(entry.get("published")) or datetime.now()

        # Extract content
        content = ""
        if "content" in entry and len(entry["content"]) > 0:
            content = entry["content"][0].get("value", "")
        elif "summary" in entry:
            content = entry.get("summary", "")

        with self.session_factory() as session:
            with database_operation(session, "create article from RSS"):
                # Create article object
                article_data = Article(
                    title=title,
                    url=url,
                    content=content,
                    published_at=published_at,
                    status="new",
                    source=source,
                    scraped_at=datetime.now(),
                )

                # Save to database
                article = self.article_crud.create(session, obj_in=article_data)

                return article.id if article else None
