"""Synchronous task implementations for the Local Newsifier project.

These are sync versions of the Celery tasks that can be used with FastAPI Background Tasks
or other sync task processing systems.
"""

import logging
from typing import Dict, List, Optional

from local_newsifier.database.engine import get_session
from local_newsifier.tools.rss_parser import parse_rss_feed

logger = logging.getLogger(__name__)


def process_article_sync(article_id: int) -> Dict:
    """
    Process an article synchronously.

    Args:
        article_id: The ID of the article to process

    Returns:
        Dict: Result information including article ID and status
    """
    logger.info(f"Processing article with ID: {article_id}")

    try:
        # Import dependencies directly for sync context
        from local_newsifier.crud.article import article as article_crud
        from local_newsifier.flows.entity_tracking_flow import EntityTrackingFlow
        from local_newsifier.flows.news_pipeline import NewsPipelineFlow

        # Get session from generator
        for session in get_session():
            if session is None:
                logger.error("Failed to create database session")
                return {
                    "article_id": article_id,
                    "status": "error",
                    "message": "Database connection failed",
                }
            # Get the article from the database
            article = article_crud.get(session, id=article_id)
            if not article:
                logger.error(f"Article with ID {article_id} not found")
                return {"article_id": article_id, "status": "error", "message": "Article not found"}

            # Create flow instances for sync context
            news_pipeline = NewsPipelineFlow()
            entity_flow = EntityTrackingFlow()

            # Process the article through the news pipeline
            if article.url:
                news_pipeline.process_url_directly(article.url)

            # Process entities in the article
            entities = entity_flow.process_article(article.id)

            return {
                "article_id": article_id,
                "status": "success",
                "processed": True,
                "entities_found": len(entities) if entities else 0,
                "article_title": article.title,
            }
    except Exception as e:
        error_msg = str(e)
        logger.exception(f"Error processing article {article_id}: {error_msg}")

        return {
            "article_id": article_id,
            "status": "error",
            "message": error_msg,
            "processed": False,
        }


def fetch_rss_feeds_sync(
    feed_urls: Optional[List[str]] = None, process_articles: bool = True
) -> Dict:
    """
    Fetch and process articles from RSS feeds synchronously.

    Args:
        feed_urls: List of RSS feed URLs to process. If None, uses feeds from database.
        process_articles: Whether to process articles after fetching (default: True)

    Returns:
        Dict: Result information including processed feeds and article counts
    """
    from local_newsifier.config.settings import settings

    if not feed_urls:
        # TODO: Get feed URLs from database instead of settings
        feed_urls = settings.RSS_FEED_URLS

    logger.info(f"Fetching articles from {len(feed_urls)} RSS feeds")

    results = {
        "feeds_processed": 0,
        "articles_found": 0,
        "articles_added": 0,
        "articles_processed": 0,
        "feeds": [],
        "status": "success",
    }

    try:
        # Import dependencies directly for sync context
        from local_newsifier.crud.article import article as article_crud
        from local_newsifier.services.article_service import ArticleService

        # Get session from generator
        for session in get_session():
            if session is None:
                logger.error("Failed to create database session")
                return {
                    "status": "error",
                    "message": "Database connection failed",
                    "feeds_processed": 0,
                    "articles_found": 0,
                    "articles_added": 0,
                    "articles_processed": 0,
                    "feeds": [],
                }

            # Import additional dependencies for ArticleService
            from local_newsifier.crud.analysis_result import analysis_result as analysis_result_crud
            from local_newsifier.crud.canonical_entity import \
                canonical_entity as canonical_entity_crud
            from local_newsifier.crud.entity import entity as entity_crud
            from local_newsifier.crud.entity_relationship import \
                entity_relationship as entity_relationship_crud
            from local_newsifier.services.entity_service import EntityService

            # Create entity service
            entity_service = EntityService(
                entity_crud=entity_crud,
                entity_relationship_crud=entity_relationship_crud,
                canonical_entity_crud=canonical_entity_crud,
                session_factory=lambda: session,
            )

            # Create article service instance with all dependencies
            article_service = ArticleService(
                article_crud=article_crud,
                analysis_result_crud=analysis_result_crud,
                entity_service=entity_service,
                session_factory=lambda: session,
            )

            for feed_url in feed_urls:
                try:
                    # Parse the RSS feed
                    feed_data = parse_rss_feed(feed_url)

                    feed_result = {
                        "url": feed_url,
                        "title": feed_data.get("title", "Unknown"),
                        "articles_found": len(feed_data.get("entries", [])),
                        "articles_added": 0,
                        "articles_processed": 0,
                        "status": "success",
                    }

                    # Process each article in the feed
                    for entry in feed_data.get("entries", []):
                        # Check if article already exists
                        existing = article_crud.get_by_url(session, url=entry.get("link", ""))

                        if not existing:
                            # Create and save new article
                            article_id = article_service.create_article_from_rss_entry(entry)
                            if article_id:
                                feed_result["articles_added"] += 1
                                results["articles_added"] += 1

                                # Process article if requested
                                if process_articles:
                                    result = process_article_sync(article_id)
                                    if result.get("status") == "success":
                                        feed_result["articles_processed"] += 1
                                        results["articles_processed"] += 1

                    results["feeds_processed"] += 1
                    results["articles_found"] += feed_result["articles_found"]
                    results["feeds"].append(feed_result)

                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Error processing feed {feed_url}: {error_msg}")
                    results["feeds"].append(
                        {
                            "url": feed_url,
                            "status": "error",
                            "message": error_msg,
                        }
                    )

            return results
    except Exception as e:
        error_msg = str(e)
        logger.exception(f"Error fetching RSS feeds: {error_msg}")
        return {
            "status": "error",
            "message": error_msg,
            "feeds_processed": 0,
            "articles_found": 0,
            "articles_added": 0,
            "articles_processed": 0,
            "feeds": [],
        }


def cleanup_old_articles_sync(days: int = 30) -> Dict:
    """
    Clean up articles older than specified days.

    Args:
        days: Number of days to keep articles (default: 30)

    Returns:
        Dict: Result with number of articles deleted
    """
    # TODO: Implement cleanup logic
    logger.info(f"Cleaning up articles older than {days} days")
    return {"status": "success", "articles_deleted": 0, "message": "Cleanup not yet implemented"}


def update_entity_profiles_sync() -> Dict:
    """
    Update entity profiles based on recent mentions.

    Returns:
        Dict: Result with number of profiles updated
    """
    # TODO: Implement entity profile update logic
    logger.info("Updating entity profiles")
    return {
        "status": "success",
        "profiles_updated": 0,
        "message": "Profile update not yet implemented",
    }
