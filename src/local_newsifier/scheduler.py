"""Simple task scheduler for periodic tasks.

Replaces Celery Beat with a lightweight Python scheduler.
"""

import logging
import threading
import time
from datetime import datetime
from typing import Callable, Dict, List, Optional

import schedule

from local_newsifier.tasks_sync import (cleanup_old_articles_sync, fetch_rss_feeds_sync,
                                        update_entity_profiles_sync)

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Simple task scheduler using the schedule library."""

    def __init__(self):
        """Initialize the task scheduler."""
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._tasks: List[Dict] = []

    def add_task(
        self, func: Callable, interval: str, at_time: Optional[str] = None, **kwargs
    ) -> None:
        """
        Add a task to the scheduler.

        Args:
            func: Function to execute
            interval: Interval type ('minutes', 'hours', 'days', 'weeks')
            at_time: Optional time to run (for daily tasks, e.g., "10:30")
            **kwargs: Arguments to pass to the function
        """
        task_info = {
            "function": func.__name__,
            "interval": interval,
            "at_time": at_time,
            "kwargs": kwargs,
            "added_at": datetime.now(),
        }

        # Schedule based on interval
        if interval == "minutes":
            schedule.every(kwargs.get("count", 1)).minutes.do(func, **kwargs)
        elif interval == "hours":
            schedule.every(kwargs.get("count", 1)).hours.do(func, **kwargs)
        elif interval == "days":
            job = schedule.every(kwargs.get("count", 1)).days
            if at_time:
                job = job.at(at_time)
            job.do(func, **kwargs)
        elif interval == "weeks":
            schedule.every(kwargs.get("count", 1)).weeks.do(func, **kwargs)
        else:
            raise ValueError(f"Invalid interval: {interval}")

        self._tasks.append(task_info)
        logger.info(f"Scheduled task: {task_info}")

    def start(self) -> None:
        """Start the scheduler in a background thread."""
        if self._running:
            logger.warning("Scheduler is already running")
            return

        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("Task scheduler started")

    def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        schedule.clear()
        self._tasks.clear()
        logger.info("Task scheduler stopped")

    def _run(self) -> None:
        """Run the scheduler loop."""
        while self._running:
            try:
                schedule.run_pending()
                time.sleep(1)  # Check every second
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(5)  # Wait a bit longer on error

    def get_tasks(self) -> List[Dict]:
        """Get list of scheduled tasks."""
        return self._tasks.copy()

    def get_next_run_times(self) -> List[Dict]:
        """Get next run times for all scheduled jobs."""
        jobs_info = []
        for job in schedule.get_jobs():
            jobs_info.append(
                {"job": str(job), "next_run": job.next_run.isoformat() if job.next_run else None}
            )
        return jobs_info


# Global scheduler instance
scheduler = TaskScheduler()


def setup_default_schedule():
    """Set up the default task schedule."""
    # Fetch RSS feeds every hour
    scheduler.add_task(fetch_rss_feeds_sync, interval="hours", count=1, process_articles=True)

    # Clean up old articles daily at 2 AM
    scheduler.add_task(
        cleanup_old_articles_sync, interval="days", count=1, at_time="02:00", days=30
    )

    # Update entity profiles every 6 hours
    scheduler.add_task(update_entity_profiles_sync, interval="hours", count=6)

    logger.info("Default schedule configured")


def start_scheduler():
    """Start the scheduler with default schedule."""
    setup_default_schedule()
    scheduler.start()
    return scheduler


def stop_scheduler():
    """Stop the scheduler."""
    scheduler.stop()
