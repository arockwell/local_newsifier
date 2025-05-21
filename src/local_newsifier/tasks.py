"""
Celery task definitions for the Local Newsifier project.
This module defines asynchronous tasks for processing articles and fetching RSS feeds.
"""

import logging
from typing import Dict, List, Optional, Iterator
import contextlib
import asyncio
from concurrent.futures import ThreadPoolExecutor

from celery import Task, current_task
from celery.signals import worker_ready
from sqlmodel import Session
from fastapi_injectable.concurrency import run_coroutine_sync

from local_newsifier.celery_app import app
from local_newsifier.config.settings import settings
from local_newsifier.database.engine import get_session
from local_newsifier.tools.rss_parser import parse_rss_feed

logger = logging.getLogger(__name__)

# Create a thread pool for running blocking operations
_thread_pool = ThreadPoolExecutor(max_workers=4)

# Utility function to get or create event loop
def get_or_create_event_loop():
    """Get the current event loop or create a new one if none exists."""
    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        logger.debug("Created new event loop for task execution")
        return loop

# Utility function to run the injectable provider function
def run_injectable_provider(provider_func):
    """
    Run an injectable provider function and handle the async/sync conversion.
    
    This function takes a fastapi-injectable provider function and properly
    handles the execution regardless of whether it's async or returns
    a coroutine.
    
    Args:
        provider_func: The provider function to run
        
    Returns:
        The result of the provider function
    """
    loop = get_or_create_event_loop()
    
    # Run the injectable provider function and get the result
    result = provider_func()
    
    # If it's a coroutine, run it with run_coroutine_sync
    if asyncio.iscoroutine(result):
        return run_coroutine_sync(result)
    
    # If it's just a regular value, return it directly
    return result

class BaseTask(Task):
    """Base Task class with common functionality for all tasks."""
    
    def __init__(self):
        """Initialize BaseTask with session factory."""
        self._session = None
        self._session_factory = None
    
    @property
    def session_factory(self):
        """Get session factory from the database engine module."""
        return get_session
    
    @property
    def db(self):
        """Get database session.
        
        Note: This property should be used for quick operations only.
        For longer operations with proper transaction management,
        use a context manager:
        
        ```
        with self.session_factory() as session:
            # database operations
        ```
        """
        if self._session is None:
            # Get a session for short-lived operations
            # The caller should not keep this session alive across async boundaries
            session_factory = self.session_factory
            if session_factory:
                self._session = next(session_factory())
        return self._session
    
    @property
    def article_service(self):
        """Get article service using provider function."""
        # Import at runtime to avoid circular dependencies
        from local_newsifier.di.providers import get_article_service
        return run_injectable_provider(get_article_service)
    
    @property
    def article_crud(self):
        """Get article CRUD using provider function."""
        # Import at runtime to avoid circular dependencies
        from local_newsifier.di.providers import get_article_crud
        return run_injectable_provider(get_article_crud)
    
    @property
    def entity_crud(self):
        """Get entity CRUD using provider function."""
        # Import at runtime to avoid circular dependencies
        from local_newsifier.di.providers import get_entity_crud
        return run_injectable_provider(get_entity_crud)
    
    @property
    def entity_service(self):
        """Get entity service using provider function."""
        # Import at runtime to avoid circular dependencies
        from local_newsifier.di.providers import get_entity_service
        return run_injectable_provider(get_entity_service)
    
    @property
    def rss_feed_service(self):
        """Get RSS feed service using provider function."""
        # Import at runtime to avoid circular dependencies
        from local_newsifier.di.providers import get_rss_feed_service
        return run_injectable_provider(get_rss_feed_service)

    def __del__(self):
        """Clean up session if it exists."""
        if self._session is not None:
            try:
                self._session.close()
                self._session = None
            except Exception as e:
                logger.error(f"Error cleaning up session: {e}")


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
    
    # Always return a response, even when exceptions occur
    try:
        # Use proper session management with context manager
        with self.session_factory() as session:
            # Get the article from the database
            article = self.article_crud.get(session, id=article_id)
            if not article:
                logger.error(f"Article with ID {article_id} not found")
                return {"article_id": article_id, "status": "error", "message": "Article not found"}
            
            # Process the article through the news pipeline
            from local_newsifier.di.providers import get_news_pipeline_flow
            news_pipeline = run_injectable_provider(get_news_pipeline_flow)
            
            if article.url:
                news_pipeline.process_url_directly(article.url)
            
            # Process entities in the article
            from local_newsifier.di.providers import get_entity_tracking_flow
            entity_flow = run_injectable_provider(get_entity_tracking_flow)
            
            entities = entity_flow.process_article(article.id)
            
            return {
                "article_id": article_id,
                "status": "success",
                "processed": True,
                "entities_found": len(entities) if entities else 0,
                "article_title": article.title,
            }
    except Exception as e:
        # Make sure we always return a valid dictionary response, even on errors
        error_msg = str(e)
        logger.exception(f"Error processing article {article_id}: {error_msg}")
        
        # This ensures we always return a dictionary, even during errors
        result = {
            "article_id": article_id, 
            "status": "error", 
            "message": error_msg,
            "processed": False
        }
        logger.debug(f"Returning error result: {result}")
        return result


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
        "status": "success"
    }
    
    try:
        # Use proper session management with context manager
        with self.session_factory() as session:
            # Get RSSParser from the provider
            from local_newsifier.di.providers import get_rss_parser
            rss_parser = run_injectable_provider(get_rss_parser)
            
            for feed_url in feed_urls:
                try:
                    # Parse the RSS feed using the parser provider
                    feed_data = parse_rss_feed(feed_url)
                    
                    feed_result = {
                        "url": feed_url,
                        "title": feed_data.get("title", "Unknown"),
                        "articles_found": len(feed_data.get("entries", [])),
                        "articles_processed": 0,
                        "status": "success"
                    }
                    
                    # Process each article in the feed
                    for entry in feed_data.get("entries", []):
                        # Check if article already exists
                        existing = self.article_crud.get_by_url(session, url=entry.get("link", ""))
                        
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
                    error_msg = str(e)
                    logger.error(f"Error processing feed {feed_url}: {error_msg}")
                    results["feeds"].append({
                        "url": feed_url,
                        "status": "error",
                        "message": error_msg,
                    })
            
            return results
    except Exception as e:
        error_msg = str(e)
        logger.exception(f"Error fetching RSS feeds: {error_msg}")
        # Make sure we always return a valid dictionary response
        return {
            "status": "error", 
            "message": error_msg,
            "feeds_processed": 0,
            "articles_found": 0,
            "articles_added": 0,
            "feeds": []
        }


@worker_ready.connect
def on_worker_ready(sender, **kwargs):
    """
    Signal handler for worker_ready event.
    Executed when a Celery worker starts up.
    """
    logger.info("Celery worker is ready")