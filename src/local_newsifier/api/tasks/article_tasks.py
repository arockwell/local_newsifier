import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict

from local_newsifier.background_task_manager import BackgroundTaskManager
from local_newsifier.di.providers import (
    get_session,
    get_article_crud,
    get_article_service,
    get_rss_feed_service,
    get_news_pipeline_flow,
    get_entity_tracking_flow,
    get_apify_service,
)

logger = logging.getLogger(__name__)


async def process_article(article_id: int) -> Dict[str, Any]:
    """Process an article using flows and update task record."""

    async def _task() -> Dict[str, Any]:
        logger.info("Processing article %s", article_id)
        try:
            with next(get_session()) as session:
                article_crud = get_article_crud()
                article = article_crud.get(session, id=article_id)
                if not article:
                    return {
                        "article_id": article_id,
                        "status": "error",
                        "message": "Article not found",
                        "processed": False,
                    }

                news_pipeline = get_news_pipeline_flow()
                if article.url:
                    news_pipeline.process_url_directly(article.url)

                entity_flow = get_entity_tracking_flow()
                entities = entity_flow.process_article(article.id)

                return {
                    "article_id": article_id,
                    "status": "success",
                    "processed": True,
                    "entities_found": len(entities) if entities else 0,
                    "article_title": article.title,
                }
        except Exception as e:  # pragma: no cover - safety net
            logger.exception("Error processing article %s: %s", article_id, e)
            return {
                "article_id": article_id,
                "status": "error",
                "message": str(e),
                "processed": False,
            }

    return await BackgroundTaskManager.run_task("process_article", _task)


async def process_rss_feed(feed_id: int) -> Dict[str, Any]:
    """Process a single RSS feed and queue article processing."""

    async def _task() -> Dict[str, Any]:
        logger.info("Processing RSS feed %s", feed_id)
        rss_service = get_rss_feed_service()

        def queue_article(article_id: int) -> None:
            asyncio.create_task(
                BackgroundTaskManager.run_task(
                    "process_article", process_article, article_id
                )
            )

        return rss_service.process_feed(feed_id, task_queue_func=queue_article)

    return await BackgroundTaskManager.run_task("process_rss_feed", _task)


async def process_apify_dataset(dataset_id: str) -> Dict[str, Any]:
    """Import items from an Apify dataset and create articles."""

    async def _task() -> Dict[str, Any]:
        logger.info("Processing Apify dataset %s", dataset_id)
        apify_service = get_apify_service()
        article_service = get_article_service()
        try:
            dataset = apify_service.get_dataset_items(dataset_id)
            items = dataset.get("items", [])
            created = 0
            for item in items:
                article_service.process_article(
                    url=item.get("url", ""),
                    content=item.get("content", ""),
                    title=item.get("title", ""),
                    published_at=datetime.now(timezone.utc),
                )
                created += 1
            return {
                "dataset_id": dataset_id,
                "items_found": len(items),
                "articles_created": created,
                "status": "success",
            }
        except Exception as e:  # pragma: no cover - safety net
            logger.exception("Error processing dataset %s: %s", dataset_id, e)
            return {
                "dataset_id": dataset_id,
                "status": "error",
                "message": str(e),
            }

    return await BackgroundTaskManager.run_task("process_apify_dataset", _task)
