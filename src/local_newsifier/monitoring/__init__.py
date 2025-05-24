"""Performance monitoring and metrics collection for Local Newsifier."""

from .decorators import monitor_db_query, monitor_performance
from .metrics import (api_active_requests, api_request_counter, api_request_duration,
                      celery_task_counter, celery_task_duration, db_connection_pool_size,
                      db_query_counter, db_query_duration, system_cpu_usage, system_memory_usage)
from .middleware import PrometheusMiddleware

__all__ = [
    # Metrics
    "api_request_counter",
    "api_request_duration",
    "api_active_requests",
    "db_query_counter",
    "db_query_duration",
    "celery_task_counter",
    "celery_task_duration",
    "system_memory_usage",
    "system_cpu_usage",
    "db_connection_pool_size",
    # Decorators
    "monitor_performance",
    "monitor_db_query",
    # Middleware
    "PrometheusMiddleware",
]
