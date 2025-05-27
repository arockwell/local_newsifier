"""Celery application configuration for the Local Newsifier project.

This module sets up the Celery application using PostgreSQL as both the broker and result backend.
"""

from celery import Celery

# Load environment variables for configuration
from local_newsifier.config.settings import settings

# Create the Celery application
app = Celery("local_newsifier")

# Configure Celery to use PostgreSQL as both broker and result backend
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

if __name__ == "__main__":
    app.start()
