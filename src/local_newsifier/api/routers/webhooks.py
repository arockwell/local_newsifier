"""
API router for webhook endpoints.

This module provides endpoints for receiving webhook notifications from
external services like Apify, validating payloads, and processing data.
"""

import json
import logging
from typing import Annotated, Any, Dict

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Request, status

from local_newsifier.api.dependencies import get_apify_webhook_service
from local_newsifier.models.webhook import ApifyWebhookResponse
from local_newsifier.services.apify_webhook_service_sync import ApifyWebhookServiceSync

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
    payload: Annotated[Dict[str, Any], Body()],
    webhook_service: Annotated[ApifyWebhookServiceSync, Depends(get_apify_webhook_service)],
    apify_webhook_signature: Annotated[str | None, Header()] = None,
) -> ApifyWebhookResponse:
    """Handle webhook notifications from Apify.

    This endpoint validates webhook payloads and creates articles from successful runs.

    Args:
        request: FastAPI request object
        payload: Parsed JSON payload
        webhook_service: Webhook service instance
        apify_webhook_signature: Optional signature header for validation

    Returns:
        ApifyWebhookResponse: Response acknowledging the webhook

    Raises:
        HTTPException: If webhook validation fails
    """
    try:
        # Convert payload dict back to string for signature validation
        raw_payload_str = json.dumps(payload, separators=(",", ":"), sort_keys=True)

        # Handle webhook using sync method
        result = webhook_service.handle_webhook(
            payload=payload,
            raw_payload=raw_payload_str,
            signature=apify_webhook_signature,
        )

        # Check if there was an error
        if result["status"] == "error":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"])

        # Return response using data from service result
        return ApifyWebhookResponse(
            status="accepted",
            message=result["message"],
            actor_id=result.get("actor_id"),
            dataset_id=result.get("dataset_id"),
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
