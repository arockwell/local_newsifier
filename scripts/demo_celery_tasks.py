#!/usr/bin/env python
"""Demo script for testing Celery tasks in the Local Newsifier project.

This script demonstrates how to submit tasks and monitor their progress.
"""

import argparse
import json
import sys
import time
from typing import Dict, List, Optional

from celery.result import AsyncResult

# Import Celery application and tasks
from local_newsifier.celery_app import app as celery_app
from local_newsifier.config.settings import settings
from local_newsifier.crud.article import ArticleCRUD
from local_newsifier.database.engine import SessionManager
from local_newsifier.tasks import analyze_entity_trends, fetch_rss_feeds, process_article


def get_task_info(task_id: str) -> Dict:
    """
    Get information about a task by its ID.

    Args:
        task_id: ID of the task to check

    Returns:
        Dict: Task status information
    """
    task_result = AsyncResult(task_id, app=celery_app)

    result = {
        "task_id": task_id,
        "status": task_result.status,
    }

    # Add additional info based on task state
    if task_result.successful():
        result["result"] = task_result.result
    elif task_result.failed():
        result["error"] = str(task_result.result)
    elif task_result.status == "PROGRESS":
        result["progress"] = task_result.info

    return result


def print_task_result(
    task_id: str, wait: bool = False, interval: int = 2, timeout: int = 60
) -> None:
    """
    Print the result of a task, with optional waiting for completion.

    Args:
        task_id: ID of the task to check
        wait: Whether to wait for task completion
        interval: Polling interval in seconds (if waiting)
        timeout: Maximum seconds to wait (if waiting)
    """
    if not wait:
        # Just print current status without waiting
        result = get_task_info(task_id)
        print(json.dumps(result, indent=2))
        return

    # Wait for task to complete
    elapsed = 0
    while elapsed < timeout:
        result = get_task_info(task_id)
        status = result.get("status")

        # Print current status
        print(f"Task {task_id} status: {status}")
        if "progress" in result:
            print(f"Progress: {json.dumps(result['progress'], indent=2)}")

        # Check if task completed or failed
        if status == "SUCCESS":
            print("Task completed successfully!")
            print(json.dumps(result.get("result", {}), indent=2))
            return
        elif status == "FAILURE":
            print("Task failed!")
            print(f"Error: {result.get('error', 'Unknown error')}")
            return

        # Wait before checking again
        time.sleep(interval)
        elapsed += interval

    print(f"Timeout after {timeout} seconds. Task is still running.")
    print(f"You can check the status later with: python {sys.argv[0]} --task-id {task_id}")


def demo_process_article(article_id: int, wait: bool = False) -> None:
    """
    Demo the process_article task.

    Args:
        article_id: ID of the article to process
        wait: Whether to wait for task completion
    """
    print(f"Submitting task to process article with ID: {article_id}")

    # Verify article exists
    with SessionManager() as session:
        article_crud = ArticleCRUD(session)
        article = article_crud.get(article_id)
        if not article:
            print(f"Error: Article with ID {article_id} not found!")
            return

        print(f"Article found: {article.title}")

    # Submit task
    task = process_article.delay(article_id)
    print(f"Task submitted with ID: {task.id}")

    # Print result
    print_task_result(task.id, wait)


def demo_fetch_rss_feeds(feed_urls: Optional[List[str]] = None, wait: bool = False) -> None:
    """
    Demo the fetch_rss_feeds task.

    Args:
        feed_urls: List of RSS feed URLs to process
        wait: Whether to wait for task completion
    """
    if not feed_urls:
        feed_urls = settings.RSS_FEED_URLS

    print(f"Submitting task to fetch {len(feed_urls)} RSS feeds:")
    for url in feed_urls:
        print(f"  - {url}")

    # Submit task
    task = fetch_rss_feeds.delay(feed_urls)
    print(f"Task submitted with ID: {task.id}")

    # Print result
    print_task_result(task.id, wait)


def demo_analyze_entity_trends(
    time_interval: str = "day",
    days_back: int = 7,
    entity_ids: Optional[List[int]] = None,
    wait: bool = False,
) -> None:
    """
    Demo the analyze_entity_trends task.

    Args:
        time_interval: Time interval for trend analysis
        days_back: Number of days to look back
        entity_ids: Optional list of entity IDs to analyze
        wait: Whether to wait for task completion
    """
    print("Submitting task to analyze entity trends:")
    print(f"  - Time interval: {time_interval}")
    print(f"  - Days back: {days_back}")
    if entity_ids:
        print(f"  - Entity IDs: {entity_ids}")
    else:
        print("  - Entity IDs: all")

    # Submit task
    task = analyze_entity_trends.delay(
        time_interval=time_interval,
        days_back=days_back,
        entity_ids=entity_ids,
    )
    print(f"Task submitted with ID: {task.id}")

    # Print result
    print_task_result(task.id, wait)


def main() -> None:
    """Main function to run the demo script."""
    parser = argparse.ArgumentParser(description="Demo Celery tasks for Local Newsifier")
    parser.add_argument(
        "--task",
        choices=["process-article", "fetch-rss", "analyze-trends", "check-status"],
        help="Task to demo",
    )
    parser.add_argument("--wait", action="store_true", help="Wait for task completion")
    parser.add_argument("--article-id", type=int, help="Article ID for article processing demo")
    parser.add_argument("--feed-urls", nargs="+", help="RSS feed URLs for fetch RSS demo")
    parser.add_argument(
        "--time-interval",
        choices=["hour", "day", "week", "month"],
        default="day",
        help="Time interval for trend analysis",
    )
    parser.add_argument("--days-back", type=int, default=7, help="Days back for trend analysis")
    parser.add_argument("--entity-ids", nargs="+", type=int, help="Entity IDs for trend analysis")
    parser.add_argument("--task-id", help="Task ID to check status")

    args = parser.parse_args()

    if args.task_id:
        # Check status of a specific task
        print(f"Checking status of task: {args.task_id}")
        print_task_result(args.task_id, args.wait)
        return

    if not args.task:
        parser.print_help()
        return

    if args.task == "process-article":
        if not args.article_id:
            print("Error: --article-id is required for process-article task")
            return
        demo_process_article(args.article_id, args.wait)

    elif args.task == "fetch-rss":
        demo_fetch_rss_feeds(args.feed_urls, args.wait)

    elif args.task == "analyze-trends":
        demo_analyze_entity_trends(
            args.time_interval,
            args.days_back,
            args.entity_ids,
            args.wait,
        )


if __name__ == "__main__":
    main()
