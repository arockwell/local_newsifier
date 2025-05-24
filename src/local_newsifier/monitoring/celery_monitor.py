"""Celery task monitoring using signals."""

import logging
import time
from typing import Any, Dict

from celery import signals
from celery.app.task import Task

from .metrics import celery_queue_length, celery_task_counter, celery_task_duration

logger = logging.getLogger(__name__)

# Store task start times
task_start_times: Dict[str, float] = {}


def setup_celery_monitoring() -> None:
    """Set up Celery task monitoring using signals."""

    @signals.task_prerun.connect
    def on_task_prerun(sender: Task, task_id: str, **kwargs) -> None:
        """Track task start."""
        task_name = sender.name
        task_start_times[task_id] = time.time()

        # Increment task counter
        celery_task_counter.labels(task_name=task_name, status="started").inc()

        logger.debug(f"Task {task_name} (ID: {task_id}) started")

    @signals.task_postrun.connect
    def on_task_postrun(sender: Task, task_id: str, **kwargs) -> None:
        """Track task completion."""
        task_name = sender.name

        # Calculate duration
        if task_id in task_start_times:
            start_time = task_start_times.pop(task_id)
            duration = time.time() - start_time

            # Record duration
            celery_task_duration.labels(task_name=task_name).observe(duration)

            logger.debug(f"Task {task_name} (ID: {task_id}) completed in {duration:.2f}s")

    @signals.task_success.connect
    def on_task_success(sender: Task, **kwargs) -> None:
        """Track successful task completion."""
        task_name = sender.name
        celery_task_counter.labels(task_name=task_name, status="success").inc()

    @signals.task_failure.connect
    def on_task_failure(sender: Task, task_id: str, exception: Exception, **kwargs) -> None:
        """Track task failure."""
        task_name = sender.name
        celery_task_counter.labels(task_name=task_name, status="failure").inc()

        # Clean up start time if present
        task_start_times.pop(task_id, None)

        logger.error(f"Task {task_name} (ID: {task_id}) failed: {str(exception)}")

    @signals.task_retry.connect
    def on_task_retry(sender: Task, **kwargs) -> None:
        """Track task retry."""
        task_name = sender.name
        celery_task_counter.labels(task_name=task_name, status="retry").inc()

    @signals.task_revoked.connect
    def on_task_revoked(sender: Task, **kwargs) -> None:
        """Track task revocation."""
        task_name = sender.name
        celery_task_counter.labels(task_name=task_name, status="revoked").inc()

    logger.info("Celery monitoring setup completed")


def update_queue_metrics(app: Any) -> None:
    """
    Update Celery queue length metrics.

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
                for queue in queues:
                    queue_name = queue.get("name", "default")

                    # Get queue length
                    # Note: This is approximate and depends on the broker
                    with app.connection_or_acquire() as conn:
                        queue_obj = conn.default_channel.queue_declare(
                            queue=queue_name, passive=True
                        )
                        if hasattr(queue_obj, "message_count"):
                            celery_queue_length.labels(queue_name=queue_name).set(
                                queue_obj.message_count
                            )

        # Also check reserved tasks
        reserved = inspect.reserved()
        if reserved:
            for worker, tasks in reserved.items():
                # Count reserved tasks as part of queue length
                for task in tasks:
                    queue_name = task.get("delivery_info", {}).get("routing_key", "default")
                    # This would increment the queue length gauge
                    # but we need to be careful not to double-count

    except Exception as e:
        logger.error(f"Error updating queue metrics: {str(e)}")
