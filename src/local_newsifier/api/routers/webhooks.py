"""
API router for webhook endpoints.

This module provides endpoints for receiving webhook notifications from
external services like Apify, validating payloads, and logging events.
"""

import logging

from fastapi import APIRouter, HTTPException, status

from local_newsifier.config.settings import settings
from local_newsifier.models.webhook import ApifyWebhookPayload, ApifyWebhookResponse

# Create router with /webhooks prefix
router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# Setup logger
logger = logging.getLogger(__name__)


def validate_webhook_secret(payload: ApifyWebhookPayload) -> bool:
    """Validate webhook secret if configured.

    Args:
        payload: The webhook payload from Apify

    Returns:
        bool: True if validation passes or no secret configured
    """
    if not settings.APIFY_WEBHOOK_SECRET:
        logger.warning("No webhook secret configured - accepting all webhooks")
        return True

    # Check if webhook includes the expected secret
    # This is a basic validation - in production you might want HMAC validation
    webhook_secret = getattr(payload, "secret", None)
    return webhook_secret == settings.APIFY_WEBHOOK_SECRET


@router.post(
    "/apify",
    response_model=ApifyWebhookResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Receive Apify webhook notifications",
    description="Endpoint for receiving webhook notifications from Apify when runs complete",
)
async def apify_webhook(payload: ApifyWebhookPayload) -> ApifyWebhookResponse:
    """Handle webhook notifications from Apify.

    This endpoint validates webhook payloads and logs events but does not
    process the data. Data processing will be added in a future enhancement.

    Args:
        payload: The webhook payload from Apify

    Returns:
        ApifyWebhookResponse: Response acknowledging the webhook

    Raises:
        HTTPException: If webhook validation fails or event type is not supported
    """
    logger.info(f"Received Apify webhook: {payload.eventType} for actor {payload.actorId}")

    # Validate webhook secret
    if not validate_webhook_secret(payload):
        logger.warning(f"Invalid webhook secret for actor {payload.actorId}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook secret",
        )

    # Log webhook details for debugging
    logger.info(
        f"Webhook details - Actor: {payload.actorId}, "
        f"Run: {payload.actorRunId}, Event: {payload.eventType}, "
        f"Dataset: {getattr(payload, 'defaultDatasetId', 'N/A')}"
    )

    # For now, just acknowledge receipt
    # TODO: Add data processing in future enhancement
    message = f"Webhook received and validated for {payload.eventType}"

    return ApifyWebhookResponse(
        status="accepted",
        message=message,
        actor_id=payload.actorId,
        dataset_id=getattr(payload, "defaultDatasetId", None),
        processing_status="webhook_recorded",
    )
