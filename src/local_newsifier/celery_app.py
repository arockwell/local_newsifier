"""
Celery application configuration for the Local Newsifier project.

This module initializes and configures the Celery application for
asynchronous task processing using PostgreSQL as both the message
broker and result backend.
"""

import logging
from typing import Dict, Any

from celery import Celery

from local_newsifier.config.settings import settings

logger = logging.getLogger(__name__)

# Initialize Celery app
app = Celery("local_newsifier")

# Configure from settings
app.conf.update(
    # Main configuration
    broker_url=settings.CELERY_BROKER_URL,
    result_backend=settings.CELERY_RESULT_BACKEND,
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    result_serializer=settings.CELERY_RESULT_SERIALIZER,
    accept_content=settings.CELERY_ACCEPT_CONTENT,
    timezone=settings.CELERY_TIMEZONE,
    task_track_started=settings.CELERY_TASK_TRACK_STARTED,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    worker_max_tasks_per_child=settings.CELERY_WORKER_MAX_TASKS_PER_CHILD,
    
    # Task routing configuration
    task_default_queue="default",
    task_routes={
        "local_newsifier.tasks.process_article": {"queue": "articles"},
        "local_newsifier.tasks.fetch_rss_feeds": {"queue": "feeds"},
        "local_newsifier.tasks.analyze_entity_trends": {"queue": "analysis"},
    },
    
    # Task execution settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    
    # For PostgreSQL transport, disable prefetching as it can cause issues with PG
    worker_prefetch_multiplier=1,
    
    # Optimize database connections for PostgreSQL
    broker_connection_timeout=30,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    broker_pool_limit=10,
)

# Configure Celery Beat for periodic tasks
app.conf.beat_schedule: Dict[str, Any] = {
    "fetch-rss-feeds-every-hour": {
        "task": "local_newsifier.tasks.fetch_rss_feeds",
        "schedule": 3600.0,  # Every hour
    },
    "analyze-trends-daily": {
        "task": "local_newsifier.tasks.analyze_entity_trends",
        "schedule": 86400.0,  # Every day
        "kwargs": {"time_interval": "day"},
    },
}

# Autodiscover tasks (will look for tasks.py in all packages)
app.autodiscover_tasks(["local_newsifier"])


def get_celery_app() -> Celery:
    """Get the Celery application instance.
    
    Returns:
        Celery: The configured Celery application instance
    """
    return app
