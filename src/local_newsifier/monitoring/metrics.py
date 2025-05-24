"""Prometheus metrics definitions for Local Newsifier."""

import os

import psutil
from prometheus_client import Counter, Gauge, Histogram, Info

# API Metrics
api_request_counter = Counter(
    "newsifier_api_requests_total",
    "Total number of API requests",
    ["method", "endpoint", "status_code"],
)

api_request_duration = Histogram(
    "newsifier_api_request_duration_seconds",
    "API request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

api_active_requests = Gauge(
    "newsifier_api_active_requests",
    "Number of active API requests",
    ["method", "endpoint"],
)

# Database Metrics
db_query_counter = Counter(
    "newsifier_db_queries_total",
    "Total number of database queries",
    ["operation", "table"],
)

db_query_duration = Histogram(
    "newsifier_db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation", "table"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

db_connection_pool_size = Gauge(
    "newsifier_db_connection_pool_size",
    "Current database connection pool size",
    ["pool_name"],
)

db_slow_query_counter = Counter(
    "newsifier_db_slow_queries_total",
    "Total number of slow database queries (>1s)",
    ["operation", "table"],
)

# Celery Task Metrics
celery_task_counter = Counter(
    "newsifier_celery_tasks_total",
    "Total number of Celery tasks",
    ["task_name", "status"],
)

celery_task_duration = Histogram(
    "newsifier_celery_task_duration_seconds",
    "Celery task duration in seconds",
    ["task_name"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
)

celery_queue_length = Gauge(
    "newsifier_celery_queue_length",
    "Number of tasks in Celery queue",
    ["queue_name"],
)

# System Metrics
system_memory_usage = Gauge(
    "newsifier_system_memory_usage_bytes",
    "Current system memory usage in bytes",
)

system_cpu_usage = Gauge(
    "newsifier_system_cpu_usage_percent",
    "Current system CPU usage percentage",
)

# Application Info
app_info = Info(
    "newsifier_app",
    "Application information",
)

# Entity Processing Metrics
entity_extraction_duration = Histogram(
    "newsifier_entity_extraction_duration_seconds",
    "Entity extraction processing time in seconds",
    ["source_type"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

entity_extraction_counter = Counter(
    "newsifier_entities_extracted_total",
    "Total number of entities extracted",
    ["entity_type", "source_type"],
)

# Sentiment Analysis Metrics
sentiment_analysis_duration = Histogram(
    "newsifier_sentiment_analysis_duration_seconds",
    "Sentiment analysis processing time in seconds",
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

# RSS Feed Processing Metrics
rss_feed_processing_duration = Histogram(
    "newsifier_rss_feed_processing_duration_seconds",
    "RSS feed processing time in seconds",
    ["feed_url"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
)

rss_feed_articles_processed = Counter(
    "newsifier_rss_feed_articles_processed_total",
    "Total number of RSS feed articles processed",
    ["feed_url", "status"],
)


# Helper functions to update system metrics
def update_system_metrics():
    """Update system resource metrics."""
    # Memory usage
    memory = psutil.virtual_memory()
    system_memory_usage.set(memory.used)

    # CPU usage (averaged over 1 second)
    cpu_percent = psutil.cpu_percent(interval=1)
    system_cpu_usage.set(cpu_percent)


def update_app_info(version: str = "0.1.0"):
    """Update application info metrics."""
    app_info.info(
        {
            "version": version,
            "python_version": os.sys.version.split()[0],
            "pid": str(os.getpid()),
        }
    )
