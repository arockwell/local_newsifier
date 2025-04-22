"""
Celery task definitions for the Local Newsifier project.
This module defines asynchronous tasks for processing articles, fetching RSS feeds,
and analyzing entity trends.
"""

import logging
from typing import Dict, List, Optional, Union

from celery import Task, current_task
from celery.signals import worker_ready

from local_newsifier.celery_app import app
from local_newsifier.config.settings import settings
from local_newsifier.crud.article import ArticleCRUD
from local_newsifier.crud.entity import EntityCRUD
from local_newsifier.database.engine import get_db
from local_newsifier.flows.entity_tracking_flow import process_entities_in_article
from local_newsifier.flows.news_pipeline import process_article as process_article_flow
from local_newsifier.flows.trend_analysis_flow import analyze_trends
from local_newsifier.services.article_service import ArticleService
from local_newsifier.tools.rss_parser import parse_rss_feed

logger = logging.getLogger(__name__)


class BaseTask(Task):
    """Base Task class with common functionality for all tasks."""

    _db = None
    _article_service = None
    _article_crud = None
    _entity_crud = None

    @property
    def db(self):
        """Get database session."""
        if self._db is None:
            self._db = next(get_db())
        return self._db

    @property
    def article_service(self):
        """Get article service."""
        if self._article_service is None:
            self._article_service = ArticleService()
        return self._article_service

    @property
    def article_crud(self):
        """Get article CRUD."""
        if self._article_crud is None:
            self._article_crud = ArticleCRUD(self.db)
        return self._article_crud

    @property
    def entity_crud(self):
        """Get entity CRUD."""
        if self._entity_crud is None:
            self._entity_crud = EntityCRUD(self.db)
        return self._entity_crud


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
        article = self.article_crud.get(article_id)
        if not article:
            logger.error(f"Article with ID {article_id} not found")
            return {"article_id": article_id, "status": "error", "message": "Article not found"}
        
        # Update the task state to indicate progress
        if current_task:
            current_task.update_state(
                state="PROGRESS", meta={"article_id": article_id, "status": "processing"}
            )
        
        # Process the article through the news pipeline
        result = process_article_flow(article)
        
        # Process entities in the article
        entity_result = process_entities_in_article(article)
        
        return {
            "article_id": article_id,
            "status": "success",
            "processed": True,
            "entities_found": len(entity_result.get("entities", [])),
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
        "articles_updated": 0,
        "feeds": [],
    }
    
    try:
        for feed_url in feed_urls:
            try:
                # Update task state for progress tracking
                if current_task:
                    current_task.update_state(
                        state="PROGRESS",
                        meta={
                            "current": feed_urls.index(feed_url) + 1,
                            "total": len(feed_urls),
                            "feed_url": feed_url,
                        },
                    )
                
                # Parse the RSS feed
                feed_data = parse_rss_feed(feed_url)
                
                feed_result = {
                    "url": feed_url,
                    "title": feed_data.get("title", "Unknown"),
                    "articles_found": len(feed_data.get("entries", [])),
                    "articles_processed": 0,
                    "status": "success",
                }
                
                # Process each article in the feed
                for entry in feed_data.get("entries", []):
                    try:
                        # Check if article already exists
                        existing = self.article_crud.get_by_url(entry.get("link", ""))
                        
                        if existing:
                            # Update existing article if needed
                            # (additional logic can be added here)
                            results["articles_updated"] += 1
                        else:
                            # Create and save new article
                            article = self.article_service.create_article_from_rss_entry(entry)
                            if article:
                                # Queue article processing task
                                process_article.delay(article.id)
                                feed_result["articles_processed"] += 1
                                results["articles_added"] += 1
                    except Exception as e:
                        logger.warning(f"Error processing feed entry: {str(e)}")
                
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


@app.task(
    bind=True, 
    base=BaseTask, 
    name="local_newsifier.tasks.analyze_entity_trends"
)
def analyze_entity_trends(
    self,
    time_interval: str = "day",
    days_back: int = 7,
    entity_ids: Optional[List[int]] = None
) -> Dict:
    """
    Analyze entity trends over a specified time period.

    Args:
        time_interval: Time interval for trend analysis ("hour", "day", "week", "month")
        days_back: Number of days to look back for trend analysis
        entity_ids: Optional list of entity IDs to analyze. If None, analyzes all entities.

    Returns:
        Dict: Result information including entity trends
    """
    logger.info(
        f"Analyzing entity trends for interval '{time_interval}', {days_back} days back"
    )
    
    try:
        # Update task state for progress tracking
        if current_task:
            current_task.update_state(
                state="PROGRESS",
                meta={
                    "status": "analyzing",
                    "time_interval": time_interval,
                    "days_back": days_back,
                },
            )
        
        # Perform trend analysis using the existing flow
        trend_results = analyze_trends(
            time_interval=time_interval,
            days_back=days_back,
            entity_ids=entity_ids,
        )
        
        # Format results for better readability
        entity_trend_data = []
        for entity_result in trend_results.get("entity_trends", []):
            entity_trend_data.append({
                "entity_id": entity_result.get("entity_id"),
                "entity_name": entity_result.get("entity_name"),
                "entity_type": entity_result.get("entity_type"),
                "trend_direction": entity_result.get("trend_direction"),
                "trend_score": entity_result.get("trend_score"),
                "mention_count": entity_result.get("mention_count"),
                "average_sentiment": entity_result.get("average_sentiment"),
            })
        
        return {
            "status": "success",
            "time_interval": time_interval,
            "days_back": days_back,
            "entities_analyzed": len(entity_trend_data),
            "entity_trends": entity_trend_data,
        }
    except Exception as e:
        logger.exception(f"Error analyzing entity trends: {str(e)}")
        return {
            "status": "error", 
            "time_interval": time_interval,
            "days_back": days_back,
            "message": str(e),
        }


@worker_ready.connect
def on_worker_ready(sender, **kwargs):
    """
    Signal handler for worker_ready event.
    Executed when a Celery worker starts up.
    """
    logger.info("Celery worker is ready")
