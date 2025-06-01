"""Simplified Apify webhook service for handling webhook notifications.

This implementation follows a simple idempotent design:
1. Receive webhook
2. Store it (idempotently using database constraints)
3. Process dataset if successful
4. Return status
"""

import hashlib
import hmac
import logging
from datetime import UTC, datetime
from typing import Dict, Optional

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from local_newsifier.crud.article import article
from local_newsifier.models.apify import ApifyWebhookRaw
from local_newsifier.models.article import Article
from local_newsifier.services.apify_service import ApifyService

logger = logging.getLogger(__name__)


class ApifyWebhookServiceSimple:
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
            for item in dataset_items:
                # Extract required fields (try common field names)
                url = item.get("url", "")
                title = item.get("title", "")
                content = (
                    item.get("content", "")
                    or item.get("text", "")
                    or item.get("body", "")
                    or item.get("description", "")
                )

                # Skip if missing required fields or content too short
                if not all([url, title]) or len(content) < 100:
                    continue

                # Skip if article already exists
                if article.get_by_url(self.session, url=url):
                    continue

                # Create article
                new_article = Article(
                    url=url,
                    title=title,
                    content=content,
                    source=item.get("source", "apify"),
                    published_at=datetime.now(UTC).replace(tzinfo=None),
                    status="published",
                    scraped_at=datetime.now(UTC).replace(tzinfo=None),
                )
                self.session.add(new_article)
                articles_created += 1

            # Commit all articles at once
            if articles_created > 0:
                self.session.commit()

            logger.info(f"Created {articles_created} articles from dataset {dataset_id}")
            return articles_created

        except Exception as e:
            logger.error(f"Error processing dataset {dataset_id}: {str(e)}", exc_info=True)
            return 0
