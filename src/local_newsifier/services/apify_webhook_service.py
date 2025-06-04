"""Simplified Apify webhook service for handling webhook notifications.

This implementation follows a simple idempotent design:
1. Receive webhook
2. Store it (idempotently using database constraints)
3. Process dataset if successful
4. Return status

Note: While maintaining the simplified structure, we've restored error handling
decorators for consistency with the rest of the codebase and to ensure proper
error classification and logging.
"""

import hashlib
import hmac
import logging
from datetime import UTC, datetime
from typing import Dict, Optional

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from local_newsifier.crud.article import article
from local_newsifier.errors.handlers import handle_apify, handle_database
from local_newsifier.models.apify import ApifyWebhookRaw
from local_newsifier.models.article import Article
from local_newsifier.services.apify_service import ApifyService

logger = logging.getLogger(__name__)


class ApifyWebhookService:
    """Simplified service for handling Apify webhooks."""

    def __init__(self, session: Session, webhook_secret: Optional[str] = None):
        """Initialize webhook service.

        Args:
            session: Database session
            webhook_secret: Optional webhook secret for signature validation
        """
        self.session = session
        self.webhook_secret = webhook_secret
        self.apify_service = ApifyService()

    @handle_apify
    def validate_signature(self, payload: str, signature: str) -> bool:
        """Validate webhook signature.

        Args:
            payload: Raw webhook payload string
            signature: Signature from Apify-Webhook-Signature header

        Returns:
            bool: True if signature is valid or no secret configured
        """
        if not self.webhook_secret:
            return True

        expected_signature = hmac.new(
            self.webhook_secret.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_signature, signature)

    @handle_database
    def handle_webhook(
        self, payload: Dict[str, any], raw_payload: str, signature: Optional[str] = None
    ) -> Dict[str, any]:
        """Handle incoming webhook notification.

        Simple idempotent implementation:
        1. Validate signature (if configured)
        2. Extract required fields
        3. Store webhook (let DB handle duplicates)
        4. Process dataset if successful run
        5. Return result

        Args:
            payload: Parsed webhook payload
            raw_payload: Raw webhook payload string for signature validation
            signature: Optional signature header value

        Returns:
            Dict with status and processing results
        """
        # Validate signature if provided
        if signature and not self.validate_signature(raw_payload, signature):
            logger.warning("Invalid webhook signature")
            return {"status": "error", "message": "Invalid signature"}

        # Extract fields from standard Apify webhook structure
        # Support both nested (v2) and flat (v1) webhook formats
        resource = payload.get("resource", {})
        if resource:
            # V2 format with nested resource
            run_id = resource.get("id", "")
            actor_id = resource.get("actId", "")
            status = resource.get("status", "")
            dataset_id = resource.get("defaultDatasetId", "")
        else:
            # V1 format with flat structure
            run_id = payload.get("actorRunId", "")
            actor_id = payload.get("actorId", "")
            status = payload.get("status", "")
            dataset_id = payload.get("defaultDatasetId", "")

        logger.info(f"Webhook received: run_id={run_id}, actor_id={actor_id}, status={status}")

        # Validate required fields
        if not run_id:
            logger.warning(f"Missing run_id in webhook payload: {payload}")
            return {"status": "error", "message": "Missing required field: run_id"}

        # Store webhook - let database handle duplicates via unique constraint
        # This is truly idempotent - no pre-checks needed
        webhook_saved = False
        try:
            webhook_raw = ApifyWebhookRaw(
                run_id=run_id,
                actor_id=actor_id or "unknown",
                status=status or "unknown",
                data=payload,
            )
            self.session.add(webhook_raw)
            self.session.commit()
            webhook_saved = True
            logger.info(f"Webhook stored: run_id={run_id}, status={status}")
        except IntegrityError:
            # Duplicate webhook - this is expected and OK
            self.session.rollback()
            logger.info(f"Duplicate webhook ignored: run_id={run_id}, status={status}")

        # Process dataset only for new successful runs
        articles_created = 0
        if webhook_saved and status == "SUCCEEDED" and dataset_id:
            try:
                articles_created = self._create_articles_from_dataset(dataset_id)
                logger.info(f"Articles created: dataset_id={dataset_id}, count={articles_created}")
            except Exception as e:
                # Log error but don't fail the webhook
                logger.error(
                    f"Failed to create articles: dataset_id={dataset_id}, error={str(e)}",
                    exc_info=True,
                )

        # Build response message
        if webhook_saved:
            message = f"Webhook processed. Articles created: {articles_created}"
        else:
            message = "Duplicate webhook ignored"

        return {
            "status": "ok",
            "run_id": run_id,
            "actor_id": actor_id,
            "dataset_id": dataset_id,
            "articles_created": articles_created,
            "is_new": webhook_saved,
            "message": message,
        }

    def _create_articles_from_dataset(self, dataset_id: str) -> int:
        """Create articles from Apify dataset.

        Simplified implementation:
        1. Fetch dataset items
        2. For each item with required fields, create article
        3. Skip duplicates based on URL
        4. Return count of created articles

        Args:
            dataset_id: Apify dataset ID

        Returns:
            Number of articles created
        """
        try:
            # Fetch dataset items
            logger.info(f"Fetching dataset: {dataset_id}")
            dataset_items = self.apify_service.client.dataset(dataset_id).list_items().items
            logger.info(f"Dataset contains {len(dataset_items)} items")

            articles_created = 0
            skipped_reasons = {"no_url": 0, "no_title": 0, "short_content": 0, "duplicate": 0}

            for idx, item in enumerate(dataset_items):
                # Log available fields for first few items
                if idx < 3:
                    logger.debug(f"Item {idx} fields: {list(item.keys())}")

                # Extract URL - required field
                url = item.get("url", "")
                if not url:
                    skipped_reasons["no_url"] += 1
                    continue

                # Extract title - required field
                title = item.get("title", "")

                # Check metadata for title if not found in top-level fields
                metadata = item.get("metadata", {})
                if not title and metadata:
                    title = metadata.get("title", "")

                if not title:
                    skipped_reasons["no_title"] += 1
                    continue

                # Extract content with improved field mapping
                content = (
                    item.get("text", "")  # Primary field from most actors
                    or item.get("markdown", "")  # Alternative format
                    or item.get("content", "")  # Legacy/custom actors
                    or item.get("body", "")  # Fallback
                )

                # Check metadata for additional content
                if not content and metadata:
                    content = metadata.get("description", "")

                # Skip if content too short (increased from 100 to 500)
                if len(content) < 500:
                    if idx < 3:
                        logger.debug(f"Item {idx} content too short: {len(content)} chars")
                    skipped_reasons["short_content"] += 1
                    continue

                # Skip if article already exists
                if article.get_by_url(self.session, url=url):
                    skipped_reasons["duplicate"] += 1
                    continue

                # Extract metadata fields if available
                published_at = datetime.now(UTC).replace(tzinfo=None)

                # Try to parse published date from metadata
                if metadata and metadata.get("publishedAt"):
                    try:
                        # Handle various date formats
                        pub_str = metadata["publishedAt"]
                        if isinstance(pub_str, str):
                            published_at = datetime.fromisoformat(
                                pub_str.replace("Z", "+00:00")
                            ).replace(tzinfo=None)
                    except Exception:
                        pass  # Use default if parsing fails

                # Create article
                new_article = Article(
                    url=url,
                    title=title,
                    content=content,
                    source=item.get("source", "apify"),
                    published_at=published_at,
                    status="published",
                    scraped_at=datetime.now(UTC).replace(tzinfo=None),
                )

                self.session.add(new_article)
                articles_created += 1

                logger.debug(f"Created article from item {idx}: {title[:50]}...")

            # Commit all articles at once
            if articles_created > 0:
                self.session.commit()

            # Log summary
            logger.info(
                f"Dataset processing complete: created={articles_created}, "
                f"skipped={sum(skipped_reasons.values())} "
                f"(no_url={skipped_reasons['no_url']}, "
                f"no_title={skipped_reasons['no_title']}, "
                f"short_content={skipped_reasons['short_content']}, "
                f"duplicate={skipped_reasons['duplicate']})"
            )

            return articles_created

        except Exception as e:
            logger.error(f"Error processing dataset {dataset_id}: {str(e)}", exc_info=True)
            return 0
