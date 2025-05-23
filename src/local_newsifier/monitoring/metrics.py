"""Prometheus metrics definitions and collection utilities."""

import logging
import time
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

from prometheus_client import Counter, Gauge, Histogram, Info, generate_latest

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

# System Info
system_info = Info("newsifier_system", "Local Newsifier system information")

# API Metrics
api_request_duration = Histogram(
    "newsifier_api_request_duration_seconds",
    "API request duration in seconds",
    ["method", "endpoint", "status"],
)

api_request_total = Counter(
    "newsifier_api_requests_total", "Total number of API requests", ["method", "endpoint", "status"]
)

api_active_requests = Gauge("newsifier_api_active_requests", "Number of active API requests")

# Database Metrics
db_query_duration = Histogram(
    "newsifier_db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation", "table"],
)

db_query_total = Counter(
    "newsifier_db_queries_total", "Total number of database queries", ["operation", "table"]
)

db_connection_pool_size = Gauge(
    "newsifier_db_connection_pool_size", "Database connection pool size"
)

db_active_connections = Gauge(
    "newsifier_db_active_connections", "Number of active database connections"
)

# Entity Processing Metrics
entity_extraction_duration = Histogram(
    "newsifier_entity_extraction_duration_seconds",
    "Entity extraction processing time in seconds",
    ["source"],
)

entity_extraction_total = Counter(
    "newsifier_entities_extracted_total", "Total number of entities extracted", ["entity_type"]
)

# Celery Task Metrics
celery_task_duration = Histogram(
    "newsifier_celery_task_duration_seconds",
    "Celery task execution duration in seconds",
    ["task_name", "status"],
)

celery_task_total = Counter(
    "newsifier_celery_tasks_total", "Total number of Celery tasks", ["task_name", "status"]
)

celery_queue_depth = Gauge(
    "newsifier_celery_queue_depth", "Number of tasks in Celery queue", ["queue_name"]
)

# Article Processing Metrics
article_processing_duration = Histogram(
    "newsifier_article_processing_duration_seconds", "Article processing duration in seconds"
)

articles_processed_total = Counter(
    "newsifier_articles_processed_total", "Total number of articles processed", ["source", "status"]
)

# RSS Feed Metrics
rss_feed_fetch_duration = Histogram(
    "newsifier_rss_feed_fetch_duration_seconds", "RSS feed fetch duration in seconds", ["feed_url"]
)

rss_feed_articles_total = Counter(
    "newsifier_rss_feed_articles_total", "Total number of articles from RSS feeds", ["feed_url"]
)

# Memory Metrics
memory_usage_bytes = Gauge(
    "newsifier_memory_usage_bytes", "Memory usage in bytes", ["type"]  # rss, vms, shared, etc.
)

# Error Metrics
errors_total = Counter(
    "newsifier_errors_total", "Total number of errors", ["component", "error_type"]
)


def timing_decorator(histogram: Histogram, labels: Optional[dict] = None) -> Callable[[F], F]:
    """Create a decorator to measure function execution time.

    Args:
        histogram: Prometheus histogram to record timing
        labels: Optional labels to add to the metric

    Returns:
        Decorator function
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                status = "success"
            except Exception as e:
                status = "error"
                logger.error(f"Error in {func.__name__}: {str(e)}")
                raise
            finally:
                duration = time.time() - start_time
                metric_labels = labels or {}
                if "status" not in metric_labels:
                    metric_labels["status"] = status

                histogram.labels(**metric_labels).observe(duration)

            return result

        return wrapper

    return decorator


def count_decorator(counter: Counter, labels: Optional[dict] = None) -> Callable[[F], F]:
    """Create a decorator to count function calls.

    Args:
        counter: Prometheus counter to increment
        labels: Optional labels to add to the metric

    Returns:
        Decorator function
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                status = "success"
            except Exception as e:
                status = "error"
                logger.error(f"Error in {func.__name__}: {str(e)}")
                raise
            finally:
                metric_labels = labels or {}
                if "status" not in metric_labels:
                    metric_labels["status"] = status

                counter.labels(**metric_labels).inc()

            return result

        return wrapper

    return decorator


def track_memory_usage():
    """Update memory usage metrics."""
    try:
        import psutil

        process = psutil.Process()
        memory_info = process.memory_info()

        memory_usage_bytes.labels(type="rss").set(memory_info.rss)
        memory_usage_bytes.labels(type="vms").set(memory_info.vms)

        # Also track shared memory if available
        if hasattr(memory_info, "shared"):
            memory_usage_bytes.labels(type="shared").set(memory_info.shared)

    except Exception as e:
        logger.error(f"Error tracking memory usage: {str(e)}")


def initialize_metrics():
    """Initialize system metrics."""
    try:
        # Set system info
        from local_newsifier.config.settings import get_settings

        settings = get_settings()

        system_info.info(
            {
                "version": "0.1.0",
                "environment": settings.LOG_LEVEL,
                "database": settings.POSTGRES_DB,
            }
        )

        # Initialize memory tracking
        track_memory_usage()

    except Exception as e:
        logger.error(f"Error initializing metrics: {str(e)}")


def get_metrics() -> bytes:
    """Generate Prometheus metrics in text format.

    Returns:
        Metrics in Prometheus text format
    """
    # Update dynamic metrics before generating
    track_memory_usage()

    return generate_latest()
