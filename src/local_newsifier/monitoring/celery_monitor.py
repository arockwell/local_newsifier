"""Celery task performance monitoring."""

import logging
import time
from typing import Any, Dict

from celery import Task
from celery.signals import (before_task_publish, task_failure, task_postrun, task_prerun,
                            task_retry, task_success)

from local_newsifier.monitoring.metrics import (celery_queue_depth, celery_task_duration,
                                                celery_task_total, errors_total)

logger = logging.getLogger(__name__)

# Store task start times
_task_start_times: Dict[str, float] = {}


def setup_celery_monitoring():
    """Set up Celery signal handlers for monitoring."""
    logger.info("Setting up Celery performance monitoring")

    # Connect signal handlers
    task_prerun.connect(_task_prerun_handler)
    task_postrun.connect(_task_postrun_handler)
    task_success.connect(_task_success_handler)
    task_failure.connect(_task_failure_handler)
    task_retry.connect(_task_retry_handler)
    before_task_publish.connect(_before_task_publish_handler)


@task_prerun.connect
def _task_prerun_handler(
    sender: Task, task_id: str, task: Task, args: tuple, kwargs: dict, **kw: Any
):
    """Handle task start event.

    Args:
        sender: Task sender
        task_id: Task ID
        task: Task instance
        args: Task arguments
        kwargs: Task keyword arguments
        **kw: Additional arguments
    """
    _task_start_times[task_id] = time.time()

    logger.debug(f"Task started: {task.name} (ID: {task_id})")


@task_postrun.connect
def _task_postrun_handler(
    sender: Task,
    task_id: str,
    task: Task,
    args: tuple,
    kwargs: dict,
    retval: Any,
    state: str,
    **kw: Any,
):
    """Handle task completion event.

    Args:
        sender: Task sender
        task_id: Task ID
        task: Task instance
        args: Task arguments
        kwargs: Task keyword arguments
        retval: Task return value
        state: Task final state
        **kw: Additional arguments
    """
    start_time = _task_start_times.pop(task_id, None)

    if start_time is not None:
        duration = time.time() - start_time

        # Map Celery state to our status
        if state == "SUCCESS":
            status = "success"
        elif state == "FAILURE":
            status = "failure"
        elif state == "RETRY":
            status = "retry"
        else:
            status = "unknown"

        # Record metrics
        labels = {"task_name": task.name, "status": status}

        celery_task_duration.labels(**labels).observe(duration)
        celery_task_total.labels(**labels).inc()

        # Log slow tasks
        if duration > 10.0:
            logger.warning(f"Slow task: {task.name} took {duration:.2f}s (status: {status})")

    logger.debug(f"Task completed: {task.name} (ID: {task_id}, State: {state})")


@task_success.connect
def _task_success_handler(sender: Task, result: Any, **kw: Any):
    """Handle successful task completion.

    Args:
        sender: Task sender
        result: Task result
        **kw: Additional arguments
    """
    logger.debug(f"Task succeeded: {sender.name}")


@task_failure.connect
def _task_failure_handler(
    sender: Task,
    task_id: str,
    exception: Exception,
    args: tuple,
    kwargs: dict,
    traceback: Any,
    einfo: Any,
    **kw: Any,
):
    """Handle task failure.

    Args:
        sender: Task sender
        task_id: Task ID
        exception: Exception that caused failure
        args: Task arguments
        kwargs: Task keyword arguments
        traceback: Exception traceback
        einfo: Exception info
        **kw: Additional arguments
    """
    error_type = type(exception).__name__

    errors_total.labels(component="celery", error_type=error_type).inc()

    logger.error(f"Task failed: {sender.name} (ID: {task_id}) - {error_type}: {str(exception)}")


@task_retry.connect
def _task_retry_handler(sender: Task, task_id: str, reason: Any, einfo: Any, **kw: Any):
    """Handle task retry.

    Args:
        sender: Task sender
        task_id: Task ID
        reason: Retry reason
        einfo: Exception info
        **kw: Additional arguments
    """
    logger.warning(f"Task retrying: {sender.name} (ID: {task_id}) - Reason: {reason}")


@before_task_publish.connect
def _before_task_publish_handler(
    sender: str, headers: dict, body: Any, properties: dict, **kw: Any
):
    """Handle task publish event.

    Args:
        sender: Task name
        headers: Task headers
        body: Task body
        properties: Task properties
        **kw: Additional arguments
    """
    # Extract routing key to determine queue
    routing_key = properties.get("routing_key", "celery")

    # This is a simple increment - in production you might want
    # to query the actual queue depth from the broker
    logger.debug(f"Task published: {sender} to queue: {routing_key}")


def update_queue_metrics(app):
    """Update Celery queue depth metrics.

    This should be called periodically to update queue metrics.

    Args:
        app: Celery app instance
    """
    try:
        # Get inspect instance
        inspect = app.control.inspect()

        # Get active queues
        active_queues = inspect.active_queues()

        if active_queues:
            for worker, queues in active_queues.items():
                for queue_info in queues:
                    queue_name = queue_info.get("name", "unknown")

                    # Get queue length (this is approximate)
                    # For accurate metrics, you'd query the broker directly
                    reserved = inspect.reserved()
                    if reserved and worker in reserved:
                        queue_length = len(reserved[worker])
                        celery_queue_depth.labels(queue_name=queue_name).set(queue_length)

    except Exception as e:
        logger.error(f"Error updating queue metrics: {str(e)}")


class MonitoredTask(Task):
    """Base task class with built-in monitoring."""

    def __call__(self, *args, **kwargs):
        """Execute task with monitoring.

        Args:
            *args: Task arguments
            **kwargs: Task keyword arguments

        Returns:
            Task result
        """
        # Task execution is already monitored by signals
        # This is here for any additional custom monitoring
        return super().__call__(*args, **kwargs)
