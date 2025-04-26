"""
Celery application configuration for the Local Newsifier project.
This module sets up the Celery application using Redis as both the broker and result backend.
"""

import os
import logging
from celery import Celery

# Load environment variables for configuration
from local_newsifier.config.settings import settings
from local_newsifier.config.logging_config import configure_logging

# Configure enhanced logging
configure_logging()
logger = logging.getLogger(__name__)

# Create the Celery application
app = Celery("local_newsifier")
logger.info("Initializing Celery application")

# Configure Celery to use Redis as both broker and result backend
app.conf.update(
    broker_url=settings.CELERY_BROKER_URL,
    result_backend=settings.CELERY_RESULT_BACKEND,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_hijack_root_logger=False,
    broker_connection_retry_on_startup=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour time limit per task
    worker_prefetch_multiplier=1,  # Fetch one task at a time
)

# Auto-discover tasks from all registered app modules
app.autodiscover_tasks(["local_newsifier.tasks"])
logger.info("Celery tasks auto-discovery complete")

if __name__ == "__main__":
    logger.info("Starting Celery worker directly")
    app.start()
    
# Celery signals for better logging
@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Log when periodic tasks are set up."""
    logger.info("Celery periodic tasks configured")

@app.task
def debug_task():
    """Task for debugging Celery configuration."""
    logger.debug("Debug task executed")
    return {"status": "success", "message": "Debug task completed"}
