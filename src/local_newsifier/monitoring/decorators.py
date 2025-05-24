"""Decorators for performance monitoring."""

import functools
import logging
import time
from contextlib import contextmanager
from typing import Any, Callable, Optional

from .metrics import (db_query_counter, db_query_duration, db_slow_query_counter,
                      entity_extraction_counter, entity_extraction_duration,
                      sentiment_analysis_duration)

logger = logging.getLogger(__name__)


def monitor_performance(
    metric_name: Optional[str] = None,
    labels: Optional[dict] = None,
) -> Callable:
    """
    Decorator to monitor function performance.

    Args:
        metric_name: Name of the metric to use (optional)
        labels: Additional labels for the metric
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # Log slow operations
                if duration > 1.0:
                    logger.warning(f"Slow operation: {func.__name__} took {duration:.2f}s")

                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Error in {func.__name__} after {duration:.2f}s: {str(e)}")
                raise

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                # Log slow operations
                if duration > 1.0:
                    logger.warning(f"Slow operation: {func.__name__} took {duration:.2f}s")

                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Error in {func.__name__} after {duration:.2f}s: {str(e)}")
                raise

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def monitor_db_query(operation: str = "select", table: str = "unknown") -> Callable:
    """
    Decorator to monitor database query performance.

    Args:
        operation: Type of database operation (select, insert, update, delete)
        table: Name of the table being queried
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()

            # Increment query counter
            db_query_counter.labels(operation=operation, table=table).inc()

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # Record duration
                db_query_duration.labels(operation=operation, table=table).observe(duration)

                # Track slow queries (>1s)
                if duration > 1.0:
                    db_slow_query_counter.labels(operation=operation, table=table).inc()
                    logger.warning(
                        f"Slow query detected: {operation} on {table} took {duration:.2f}s"
                    )

                return result

            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Database error in {operation} on {table} after {duration:.2f}s: {str(e)}"
                )
                raise

        return wrapper

    return decorator


def monitor_entity_extraction(source_type: str = "unknown") -> Callable:
    """
    Decorator to monitor entity extraction performance.

    Args:
        source_type: Type of content source (article, rss, apify, etc.)
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # Record duration
                entity_extraction_duration.labels(source_type=source_type).observe(duration)

                # Count entities if result is a list
                if isinstance(result, list):
                    for entity in result:
                        if hasattr(entity, "entity_type"):
                            entity_extraction_counter.labels(
                                entity_type=entity.entity_type, source_type=source_type
                            ).inc()

                return result

            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Entity extraction error after {duration:.2f}s: {str(e)}")
                raise

        return wrapper

    return decorator


def monitor_sentiment_analysis() -> Callable:
    """Decorator to monitor sentiment analysis performance."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # Record duration
                sentiment_analysis_duration.observe(duration)

                return result

            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Sentiment analysis error after {duration:.2f}s: {str(e)}")
                raise

        return wrapper

    return decorator


@contextmanager
def monitor_operation(operation_name: str, **labels):
    """
    Context manager for monitoring arbitrary operations.

    Usage:
        with monitor_operation("data_processing", stage="validation"):
            # Your code here
            pass
    """
    start_time = time.time()

    try:
        yield
        duration = time.time() - start_time

        # Log the operation
        logger.info(
            f"Operation '{operation_name}' completed in {duration:.2f}s",
            extra={"labels": labels, "duration": duration},
        )

    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"Operation '{operation_name}' failed after {duration:.2f}s: {str(e)}",
            extra={"labels": labels, "duration": duration},
        )
        raise


# Fix missing import
import asyncio
