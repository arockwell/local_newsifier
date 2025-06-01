"""Minimal Apify webhook service for handling webhook notifications."""

import hashlib
import hmac
import logging
from datetime import UTC, datetime
from typing import Dict, Optional

from sqlmodel import Session, select

from local_newsifier.crud.article import article
from local_newsifier.errors.error import ServiceError
from local_newsifier.errors.handlers import handle_apify, handle_database
from local_newsifier.models.apify import ApifyWebhookRaw
from local_newsifier.models.article import Article
from local_newsifier.services.apify_service import ApifyService

logger = logging.getLogger(__name__)


class ApifyWebhookService:
    """Minimal service for handling Apify webhooks."""

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

        Args:
            payload: Parsed webhook payload
            raw_payload: Raw webhook payload string for signature validation
            signature: Optional signature header value

        Returns:
            Dict with status and any error information
        """
        # Validate signature if provided
        if signature and not self.validate_signature(raw_payload, signature):
            logger.warning("Invalid webhook signature")
            return {"status": "error", "message": "Invalid signature"}

        # Extract from nested structure
        event_data = payload.get("eventData", {})
        resource = payload.get("resource", {})

        # Extract key fields from nested locations with fallbacks
        run_id = event_data.get("actorRunId", "") or resource.get("id", "")
        actor_id = event_data.get("actorId", "") or resource.get("actId", "")
        status = resource.get("status", "")

        if not all([run_id, actor_id, status]):
            logger.warning("Missing required webhook fields")
            return {"status": "error", "message": "Missing required fields"}

        # Check for duplicate
        existing = self.session.exec(
            select(ApifyWebhookRaw).where(ApifyWebhookRaw.run_id == run_id)
        ).first()

        if existing:
            logger.info(f"Duplicate webhook for run_id: {run_id}")
            return {"status": "ok", "message": "Duplicate webhook ignored"}

        # Convert datetime strings to naive UTC datetime objects
        payload_copy = payload.copy()
        for field in ["createdAt", "startedAt", "finishedAt"]:
            if field in payload_copy and payload_copy[field]:
                try:
                    # Parse ISO format datetime string
                    dt_str = payload_copy[field]
                    # Handle 'Z' suffix for UTC
                    if dt_str.endswith("Z"):
                        dt_str = dt_str[:-1] + "+00:00"
                    dt = datetime.fromisoformat(dt_str)
                    # Convert to naive UTC datetime
                    payload_copy[field] = dt.replace(tzinfo=None)
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Error parsing datetime field {field}: {e}")
                    # Keep original value if parsing fails
                    pass

        # Save raw webhook data
        webhook_raw = ApifyWebhookRaw(
            run_id=run_id, actor_id=actor_id, status=status, data=payload_copy
        )
        self.session.add(webhook_raw)

        # If successful run, try to create articles
        articles_created = 0
        if status == "SUCCEEDED":
            # Extract dataset ID from resource section
            dataset_id = resource.get("defaultDatasetId", "")
            if dataset_id:
                try:
                    articles_created = self._create_articles_from_dataset(dataset_id)
                except ServiceError as e:
                    logger.error(f"Failed to create articles from dataset {dataset_id}: {e}")
                    # Don't fail the whole webhook processing

        self.session.commit()

        return {
            "status": "ok",
            "message": f"Webhook processed. Articles created: {articles_created}",
            "run_id": run_id,
            "articles_created": articles_created,
        }

    @handle_apify
    def _create_articles_from_dataset(self, dataset_id: str) -> int:
        """Create articles from Apify dataset.

        Args:
            dataset_id: Apify dataset ID

        Returns:
            Number of articles created
        """
        # Fetch dataset items
        dataset_items = self.apify_service.client.dataset(dataset_id).list_items().items

        articles_created = 0
        for item in dataset_items:
            # Extract fields with fallbacks
            url = item.get("url", "")
            title = item.get("title", "")
            content = item.get("content", "") or item.get("text", "") or item.get("body", "")

            # Skip if missing required fields
            if not all([url, title, content]):
                continue

            # Skip if content too short
            if len(content) < 100:
                continue

            # Check if article already exists
            existing = article.get_by_url(self.session, url=url)
            if existing:
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

        return articles_created
