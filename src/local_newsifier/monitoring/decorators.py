"""Performance monitoring decorators for services and functions."""

import logging
import time
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

from local_newsifier.monitoring.metrics import (article_processing_duration,
                                                entity_extraction_duration, errors_total,
                                                rss_feed_fetch_duration)

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def monitor_performance(
    metric_name: Optional[str] = None, labels: Optional[dict] = None
) -> Callable[[F], F]:
    """Generic performance monitoring decorator.

    Args:
        metric_name: Name of the function for logging
        labels: Additional labels for metrics

    Returns:
        Decorator function
    """

    def decorator(func: F) -> F:
        name = metric_name or func.__name__

        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                status = "success"

            except Exception as e:
                status = "error"
                error_type = type(e).__name__

                errors_total.labels(component=name, error_type=error_type).inc()

                logger.error(f"Error in {name}: {error_type} - {str(e)}")
                raise

            finally:
                duration = time.time() - start_time

                # Log performance
                logger.debug(f"{name} completed in {duration:.3f}s (status: {status})")

                # Log slow operations
                if duration > 1.0:
                    logger.warning(f"Slow operation: {name} took {duration:.2f}s")

            return result

        return wrapper

    return decorator


def monitor_article_processing(func: F) -> F:
    """Monitor article processing performance.

    Args:
        func: Function to monitor

    Returns:
        Wrapped function
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()

        try:
            result = func(*args, **kwargs)

            # Record success
            duration = time.time() - start_time
            article_processing_duration.observe(duration)

            logger.info(f"Article processing completed in {duration:.3f}s")

            return result

        except Exception as e:
            # Record error
            errors_total.labels(component="article_processing", error_type=type(e).__name__).inc()

            logger.error(f"Article processing failed: {str(e)}")
            raise

    return wrapper


def monitor_entity_extraction(source: str = "unknown") -> Callable[[F], F]:
    """Monitor entity extraction performance.

    Args:
        source: Source of the extraction (e.g., 'spacy', 'custom')

    Returns:
        Decorator function
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = func(*args, **kwargs)

                # Record success
                duration = time.time() - start_time
                entity_extraction_duration.labels(source=source).observe(duration)

                # Log entity count if available
                if isinstance(result, (list, tuple)):
                    entity_count = len(result)
                    logger.info(
                        f"Entity extraction ({source}) completed in {duration:.3f}s, "
                        f"found {entity_count} entities"
                    )
                else:
                    logger.info(f"Entity extraction ({source}) completed in {duration:.3f}s")

                return result

            except Exception as e:
                # Record error
                errors_total.labels(
                    component="entity_extraction", error_type=type(e).__name__
                ).inc()

                logger.error(f"Entity extraction ({source}) failed: {str(e)}")
                raise

        return wrapper

    return decorator


def monitor_rss_feed_fetch(feed_url: Optional[str] = None) -> Callable[[F], F]:
    """Monitor RSS feed fetching performance.

    Args:
        feed_url: URL of the RSS feed

    Returns:
        Decorator function
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Try to extract feed URL from arguments if not provided
            url = feed_url
            if not url and args:
                url = str(args[0]) if args else None

            start_time = time.time()

            try:
                result = func(*args, **kwargs)

                # Record success
                duration = time.time() - start_time
                rss_feed_fetch_duration.labels(feed_url=url).observe(duration)

                # Log article count if available
                if isinstance(result, dict) and "entries" in result:
                    article_count = len(result["entries"])
                    logger.info(
                        f"RSS feed fetch ({url}) completed in {duration:.3f}s, "
                        f"found {article_count} articles"
                    )
                else:
                    logger.info(f"RSS feed fetch ({url}) completed in {duration:.3f}s")

                return result

            except Exception as e:
                # Record error
                errors_total.labels(component="rss_feed_fetch", error_type=type(e).__name__).inc()

                logger.error(f"RSS feed fetch ({url}) failed: {str(e)}")
                raise

        return wrapper

    return decorator


def monitor_database_operation(
    operation: str = "unknown", table: str = "unknown"
) -> Callable[[F], F]:
    """Monitor database operations (as a backup to SQLAlchemy events).

    Args:
        operation: Type of operation (select, insert, update, delete)
        table: Table name

    Returns:
        Decorator function
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # Log slow operations
                if duration > 0.5:
                    logger.warning(
                        f"Slow database operation: {operation} on {table} " f"took {duration:.2f}s"
                    )

                return result

            except Exception as e:
                # Record error
                errors_total.labels(component="database", error_type=type(e).__name__).inc()

                logger.error(f"Database operation failed: {operation} on {table} - {str(e)}")
                raise

        return wrapper

    return decorator
