"""
Celery task definitions for the Local Newsifier project.
This module defines asynchronous tasks for processing articles and fetching RSS feeds.
"""

import logging
from typing import Dict, List, Optional, Iterator

from celery import Task, current_task
from celery.signals import worker_ready
from sqlmodel import Session

from local_newsifier.celery_app import app
from local_newsifier.config.settings import settings
from local_newsifier.crud.article import CRUDArticle
from local_newsifier.crud.entity import CRUDEntity
from local_newsifier.database.engine import get_session, SessionManager
from local_newsifier.flows.entity_tracking_flow import EntityTrackingFlow
from local_newsifier.flows.news_pipeline import NewsPipelineFlow
from local_newsifier.services.article_service import ArticleService
from local_newsifier.tools.rss_parser import parse_rss_feed

logger = logging.getLogger(__name__)


# Expose get_db as a module-level function for tests
def get_db() -> Iterator[Session]:
    """Get a database session generator."""
    return get_session()


# Import models
from local_newsifier.models.article import Article
from local_newsifier.models.entity import Entity

# Import models
from local_newsifier.models.analysis_result import AnalysisResult
from local_newsifier.crud.analysis_result import CRUDAnalysisResult
from local_newsifier.services.entity_service import EntityService
from local_newsifier.crud.canonical_entity import canonical_entity
from local_newsifier.crud.entity_mention_context import entity_mention_context
from local_newsifier.crud.entity_profile import entity_profile
from local_newsifier.tools.extraction.entity_extractor import EntityExtractor
from local_newsifier.tools.analysis.context_analyzer import ContextAnalyzer
from local_newsifier.tools.resolution.entity_resolver import EntityResolver

# Initialize CRUD instances
_crud_article = CRUDArticle(Article)
_crud_entity = CRUDEntity(Entity)
_crud_analysis_result = CRUDAnalysisResult(AnalysisResult)

# Create entity service for article service dependency
_entity_service = EntityService(
    entity_crud=_crud_entity,
    canonical_entity_crud=canonical_entity,
    entity_mention_context_crud=entity_mention_context,
    entity_profile_crud=entity_profile,
    article_crud=_crud_article,
    entity_extractor=EntityExtractor(),
    context_analyzer=ContextAnalyzer(),
    entity_resolver=EntityResolver(),
    session_factory=get_session
)

# Create article service
_service_article = ArticleService(
    article_crud=_crud_article,
    analysis_result_crud=_crud_analysis_result,
    entity_service=_entity_service,
    session_factory=lambda: SessionManager()  # Use SessionManager which is a context manager
)

# These are exported for tests and services/__init__.py
article_crud = _crud_article
entity_crud = _crud_entity
article_service = _service_article

# Also export entity_service for services/__init__.py
entity_service = _entity_service

class BaseTask(Task):
    """Base Task class with common functionality for all tasks."""
    
    _db = None
    
    @property
    def db(self):
        """Get database session."""
        if self._db is None:
            self._db = next(get_db())
        return self._db
    
    @property
    def article_service(self):
        """Get article service."""
        return _service_article
    
    @property
    def article_crud(self):
        """Get article CRUD."""
        return _crud_article
    
    @property
    def entity_crud(self):
        """Get entity CRUD."""
        return _crud_entity


@app.task(bind=True, base=BaseTask, name="local_newsifier.tasks.process_article")
def process_article(self, article_id: int) -> Dict:
    """
    Process an article asynchronously.

    Args:
        article_id: The ID of the article to process

    Returns:
        Dict: Result information including article ID and status
    """
    logger.info(f"Processing article with ID: {article_id}")
    
    try:
        # Get the article from the database
        article = self.article_crud.get(self.db, id=article_id)
        if not article:
            logger.error(f"Article with ID {article_id} not found")
            return {"article_id": article_id, "status": "error", "message": "Article not found"}
        
        # Process the article through the news pipeline
        news_pipeline = NewsPipelineFlow()
        if article.url:
            news_pipeline.process_url_directly(article.url)
        
        # Process entities in the article
        entity_flow = EntityTrackingFlow()
        entities = entity_flow.process_article(article.id)
        
        return {
            "article_id": article_id,
            "status": "success",
            "processed": True,
            "entities_found": len(entities) if entities else 0,
            "article_title": article.title,
        }
    except Exception as e:
        logger.exception(f"Error processing article {article_id}: {str(e)}")
        return {"article_id": article_id, "status": "error", "message": str(e)}


@app.task(bind=True, base=BaseTask, name="local_newsifier.tasks.fetch_rss_feeds")
def fetch_rss_feeds(self, feed_urls: Optional[List[str]] = None) -> Dict:
    """
    Fetch and process articles from RSS feeds.

    Args:
        feed_urls: List of RSS feed URLs to process. If None, uses default feeds from settings.

    Returns:
        Dict: Result information including processed feeds and article counts
    """
    if not feed_urls:
        feed_urls = settings.RSS_FEED_URLS
    
    logger.info(f"Fetching articles from {len(feed_urls)} RSS feeds")
    
    results = {
        "feeds_processed": 0,
        "articles_found": 0,
        "articles_added": 0,
        "feeds": [],
    }
    
    try:
        for feed_url in feed_urls:
            try:
                # Parse the RSS feed
                feed_data = parse_rss_feed(feed_url)
                
                feed_result = {
                    "url": feed_url,
                    "title": feed_data.get("title", "Unknown"),
                    "articles_found": len(feed_data.get("entries", [])),
                    "articles_processed": 0,
                }
                
                # Process each article in the feed
                for entry in feed_data.get("entries", []):
                    # Check if article already exists
                    existing = self.article_crud.get_by_url(self.db, url=entry.get("link", ""))
                    
                    if not existing:
                        # Create and save new article
                        article_id = self.article_service.create_article_from_rss_entry(entry)
                        if article_id:
                            # Queue article processing task
                            process_article.delay(article_id)
                            feed_result["articles_processed"] += 1
                            results["articles_added"] += 1
                
                results["feeds_processed"] += 1
                results["articles_found"] += feed_result["articles_found"]
                results["feeds"].append(feed_result)
                
            except Exception as e:
                logger.error(f"Error processing feed {feed_url}: {str(e)}")
                results["feeds"].append({
                    "url": feed_url,
                    "status": "error",
                    "message": str(e),
                })
        
        return results
    except Exception as e:
        logger.exception(f"Error fetching RSS feeds: {str(e)}")
        return {"status": "error", "message": str(e)}


@worker_ready.connect
def on_worker_ready(sender, **kwargs):
    """
    Signal handler for worker_ready event.
    Executed when a Celery worker starts up.
    """
    logger.info("Celery worker is ready")
