"""
API router for webhook endpoints.

This module provides endpoints for receiving webhook notifications from
external services like Apify, validating payloads, and processing data.
"""

import json
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlmodel import Session

from local_newsifier.api.dependencies import get_session
from local_newsifier.config.settings import settings
from local_newsifier.models.webhook import ApifyWebhookResponse
from local_newsifier.services.apify_webhook_service import ApifyWebhookService

# Create router with /webhooks prefix
router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# Setup logger
logger = logging.getLogger(__name__)


@router.post(
    "/apify",
    response_model=ApifyWebhookResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Receive Apify webhook notifications",
    description="Endpoint for receiving webhook notifications from Apify when runs complete",
)
def apify_webhook(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    apify_webhook_signature: Annotated[str | None, Header()] = None,
) -> ApifyWebhookResponse:
    """Handle webhook notifications from Apify.

    This endpoint validates webhook payloads and creates articles from successful runs.

    Args:
        request: FastAPI request object containing raw body
        session: Database session
        apify_webhook_signature: Optional signature header for validation

    Returns:
        ApifyWebhookResponse: Response acknowledging the webhook

    Raises:
        HTTPException: If webhook validation fails
    """
    try:
        # Get raw payload for signature validation
        raw_payload = request.body()
        raw_payload_str = raw_payload.decode("utf-8")

        # Parse payload
        payload_dict = json.loads(raw_payload_str)

        # Initialize sync webhook service
        webhook_service = ApifyWebhookService(
            session=session, webhook_secret=settings.APIFY_WEBHOOK_SECRET
        )

        # Handle webhook using sync method
        result = webhook_service.handle_webhook(
            payload=payload_dict,
            raw_payload=raw_payload_str,
            signature=apify_webhook_signature,
        )

        # Check if there was an error
        if result["status"] == "error":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"])

        # Return response
        return ApifyWebhookResponse(
            status="accepted",
            message=result["message"],
            actor_id=payload_dict.get("actorId"),
            dataset_id=payload_dict.get("defaultDatasetId"),
            processing_status="completed",
        )

    except HTTPException:
        # Re-raise HTTPException so FastAPI handles it properly
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return ApifyWebhookResponse(
            status="error", message=f"Error processing webhook: {str(e)}", error=str(e)
        )
