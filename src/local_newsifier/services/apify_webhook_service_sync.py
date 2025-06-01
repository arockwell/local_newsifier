"""Sync Apify webhook service for handling webhook notifications.

This is a duplicate of the existing sync ApifyWebhookService but renamed
to clearly distinguish it from the async version during the transition.
"""

import hashlib
import hmac
import json
import logging
import time
from datetime import UTC, datetime
from typing import Dict, Optional

from sqlmodel import Session, select

from local_newsifier.crud.article import article
from local_newsifier.models.apify import ApifyWebhookRaw
from local_newsifier.models.article import Article
from local_newsifier.services.apify_service import ApifyService

logger = logging.getLogger(__name__)


class ApifyWebhookServiceSync:
    """Sync service for handling Apify webhooks."""

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
            logger.debug("Signature validation: no webhook secret configured, skipping validation")
            return True

        expected_signature = hmac.new(
            self.webhook_secret.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()

        is_valid = hmac.compare_digest(expected_signature, signature)
        logger.info(f"Signature validation: valid={is_valid}")
        return is_valid

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
        # Start timing
        start_time = time.time()

        # Add debug logging
        logger.debug(f"Received webhook payload: {payload}")

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

        # Log extracted values
        logger.info(f"Payload extraction: run_id={run_id}, actor_id={actor_id}, status={status}")
        logger.debug(
            f"Extracted fields - run_id: '{run_id}', actor_id: '{actor_id}', status: '{status}'"
        )
        logger.debug(f"Event data: {event_data}")
        logger.debug(f"Resource: {resource}")

        if not all([run_id, actor_id, status]):
            missing_fields = []
            if not run_id:
                missing_fields.append("actorRunId")
            if not actor_id:
                missing_fields.append("actorId")
            if not status:
                missing_fields.append("status")

            logger.warning(f"Missing required webhook fields: {missing_fields}")
            logger.warning(f"Full payload: {payload}")
            return {
                "status": "error",
                "message": f"Missing required fields: {', '.join(missing_fields)}",
            }

        # Check for duplicate with timing
        duplicate_check_start = time.time()
        logger.info(f"Checking for duplicate webhook: run_id={run_id}, status={status}")
        existing = self.session.exec(
            select(ApifyWebhookRaw).where(
                ApifyWebhookRaw.run_id == run_id, ApifyWebhookRaw.status == status
            )
        ).first()
        duplicate_check_time = time.time() - duplicate_check_start
        logger.debug(f"Duplicate check completed in {duplicate_check_time:.3f}s")

        if existing:
            logger.info(f"Duplicate webhook detected: run_id={run_id}, status={status}, ignoring")
            return {"status": "ok", "message": "Duplicate webhook ignored"}

        logger.info(f"Webhook not duplicate, proceeding with processing: run_id={run_id}")

        # Convert datetime strings to string format for JSON storage
        # This avoids timezone issues when storing in JSONB
        payload_copy = payload.copy()
        for field in ["createdAt", "startedAt", "finishedAt"]:
            if field in payload_copy and payload_copy[field]:
                # Keep datetime strings as strings in the JSON field
                # This preserves the original format and avoids timezone issues
                pass

        # Save raw webhook data with proper error handling
        try:
            webhook_raw = ApifyWebhookRaw(
                run_id=run_id, actor_id=actor_id, status=status, data=payload_copy
            )
            self.session.add(webhook_raw)
            self.session.flush()  # Force the constraint check
            logger.info(f"Storing raw webhook data: run_id={run_id}")
        except Exception as e:
            # Check if it's a duplicate key violation
            from sqlalchemy.exc import IntegrityError

            if isinstance(e, IntegrityError) and "ix_apify_webhook_raw_run_id" in str(e):
                self.session.rollback()
                logger.warning(f"Duplicate webhook received for run_id: {run_id}, status: {status}")
                # Return success to prevent Apify retries
                return {
                    "status": "ok",
                    "message": "Webhook already processed (duplicate)",
                    "run_id": run_id,
                    "actor_id": actor_id,
                    "dataset_id": resource.get("defaultDatasetId", ""),
                    "articles_created": 0,
                }
            # Re-raise other errors
            raise

        # If successful run, try to create articles
        articles_created = 0
        dataset_id = resource.get("defaultDatasetId", "")

        if status == "SUCCEEDED":
            if dataset_id:
                logger.info(f"Actor run succeeded, fetching dataset: dataset_id={dataset_id}")
                try:
                    article_start_time = time.time()
                    articles_created = self._create_articles_from_dataset(dataset_id)
                    article_creation_time = time.time() - article_start_time
                    logger.info(
                        f"Article creation completed: articles_created={articles_created}, "
                        f"duration={article_creation_time:.3f}s"
                    )
                except Exception as e:
                    logger.error(
                        f"Error creating articles from webhook: run_id={run_id}, "
                        f"dataset_id={dataset_id}, error={str(e)}",
                        exc_info=True,
                    )
                    logger.debug(f"Webhook payload on article error: {payload}")
                    # Don't fail the webhook - just log the error
            else:
                logger.warning(f"No dataset ID found in successful run: run_id={run_id}")
        else:
            logger.info(f"Actor run status not SUCCEEDED ({status}), skipping article creation")

        self.session.commit()
        logger.info(f"Webhook data saved: run_id={run_id}")

        # Total processing time
        total_time = time.time() - start_time
        logger.info(
            f"Webhook processing complete: run_id={run_id}, articles_created={articles_created}, "
            f"duration={total_time:.3f}s"
        )

        return {
            "status": "ok",
            "message": f"Webhook processed. Articles created: {articles_created}",
            "run_id": run_id,
            "actor_id": actor_id,
            "dataset_id": dataset_id,
            "articles_created": articles_created,
        }

    def _create_articles_from_dataset(self, dataset_id: str) -> int:
        """Create articles from Apify dataset.

        Args:
            dataset_id: Apify dataset ID

        Returns:
            Number of articles created
        """
        try:
            # Fetch dataset items with timing
            fetch_start = time.time()
            logger.info(f"Fetching dataset: dataset_id={dataset_id}")
            dataset_items = self.apify_service.client.dataset(dataset_id).list_items().items
            fetch_time = time.time() - fetch_start
            logger.info(
                f"Dataset items received: count={len(dataset_items)}, "
                f"fetch_duration={fetch_time:.3f}s"
            )

            # EMERGENCY LOGGING: Log structure of first item
            if dataset_items:
                logger.info("=== DATASET ITEM STRUCTURE ===")
                logger.info(f"First item keys: {list(dataset_items[0].keys())}")
                logger.info(
                    f"First item sample: {json.dumps(dataset_items[0], indent=2)[:1000]}..."
                )  # First 1000 chars

            articles_created = 0
            articles_skipped = 0
            skip_reasons = {"missing_fields": 0, "short_content": 0, "duplicate_url": 0}

            for idx, item in enumerate(dataset_items, 1):
                # Extract fields with fallbacks
                url = item.get("url", "")
                title = item.get("title", "")
                content = item.get("content", "") or item.get("text", "") or item.get("body", "")

                logger.info(f"Processing article {idx}/{len(dataset_items)}: url={url}")

                # Track field extraction fallbacks
                if not item.get("content") and (item.get("text") or item.get("body")):
                    logger.debug(
                        f"Using fallback field for content: "
                        f"{'text' if item.get('text') else 'body'}"
                    )

                # Skip if missing required fields
                if not all([url, title, content]):
                    missing = []
                    if not url:
                        missing.append("url")
                    if not title:
                        missing.append("title")
                    if not content:
                        missing.append("content")
                    logger.info(
                        f"Skipping article: url={url or 'N/A'}, "
                        f"reason=missing_fields ({', '.join(missing)})"
                    )
                    articles_skipped += 1
                    skip_reasons["missing_fields"] += 1
                    continue

                # Skip if content too short
                content_length = len(content)
                if content_length < 100:
                    logger.info(
                        f"Skipping article: url={url}, reason=short_content "
                        f"(length={content_length})"
                    )
                    articles_skipped += 1
                    skip_reasons["short_content"] += 1
                    continue

                # Log content validation
                logger.debug(f"Content validation passed: length={content_length}")

                # Check if article already exists
                existing = article.get_by_url(self.session, url=url)
                if existing:
                    logger.info(
                        f"Skipping article: url={url}, reason=duplicate_url "
                        f"(existing_id={existing.id})"
                    )
                    articles_skipped += 1
                    skip_reasons["duplicate_url"] += 1
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
                self.session.flush()  # Get the ID
                articles_created += 1
                logger.info(
                    f"Article created: id={new_article.id}, url={url}, "
                    f"title_length={len(title)}, content_length={content_length}"
                )

            # Log summary
            logger.info(
                f"Article processing summary: total={len(dataset_items)}, "
                f"created={articles_created}, skipped={articles_skipped}"
            )
            if articles_skipped > 0:
                logger.info(
                    f"Skip reasons: missing_fields={skip_reasons['missing_fields']}, "
                    f"short_content={skip_reasons['short_content']}, "
                    f"duplicate_url={skip_reasons['duplicate_url']}"
                )

            return articles_created

        except Exception as e:
            logger.error(f"Error fetching dataset {dataset_id}: {str(e)}", exc_info=True)
            # Try to get more specific error info
            if hasattr(e, "response"):
                logger.error(
                    f"Apify API error: status={getattr(e.response, 'status_code', 'N/A')}, "
                    f"response={getattr(e.response, 'text', 'N/A')}"
                )
            return 0
