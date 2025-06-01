"""
Simplified API router for webhook endpoints.

This module provides a clean, simple webhook handler that:
1. Accepts webhooks
2. Returns proper HTTP status codes
3. Lets Apify handle retries naturally
"""

import logging
from typing import Annotated, Any, Dict

from fastapi import APIRouter, Body, Depends, Header, Request
from fastapi import status as http_status
from sqlmodel import Session

from local_newsifier.api.dependencies import get_session
from local_newsifier.config.settings import get_settings
from local_newsifier.services.apify_webhook_service_simple import ApifyWebhookServiceSimple

# Create router with /webhooks prefix
router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# Setup logger
logger = logging.getLogger(__name__)


def get_webhook_service(
    session: Annotated[Session, Depends(get_session)]
) -> ApifyWebhookServiceSimple:
    """Get webhook service instance."""
    settings = get_settings()
    webhook_secret = settings.APIFY_WEBHOOK_SECRET
    return ApifyWebhookServiceSimple(session=session, webhook_secret=webhook_secret)


@router.post(
    "/apify",
    status_code=http_status.HTTP_202_ACCEPTED,
    summary="Receive Apify webhook notifications",
    description="Simple endpoint that accepts Apify webhooks and processes them idempotently",
)
def apify_webhook(
    request: Request,
    payload: Annotated[Dict[str, Any], Body()],
    webhook_service: Annotated[ApifyWebhookServiceSimple, Depends(get_webhook_service)],
    apify_webhook_signature: Annotated[str | None, Header()] = None,
) -> Dict[str, Any]:
    """Handle webhook notifications from Apify.

    Simple implementation:
    - Accept webhook
    - Validate signature (if configured)
    - Store webhook data
    - Process if successful
    - Return 202 Accepted

    If there's an error, return proper HTTP error code to trigger
    Apify's exponential backoff retry mechanism.

    Args:
        request: FastAPI request object
        payload: Parsed JSON payload from Apify
        webhook_service: Injected webhook service
        apify_webhook_signature: Optional signature header

    Returns:
        Simple acknowledgment response
    """
    # Convert payload to string for signature validation
    import json

    raw_payload = json.dumps(payload, separators=(",", ":"), sort_keys=True)

    # Process webhook
    result = webhook_service.handle_webhook(
        payload=payload,
        raw_payload=raw_payload,
        signature=apify_webhook_signature,
    )

    # Return error status if validation failed
    if result["status"] == "error":
        # Return 400 Bad Request for invalid webhooks
        # This tells Apify not to retry invalid requests
        from fastapi import HTTPException

        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=result["message"])

    # Return simple success response
    # 202 Accepted is appropriate for webhooks that are processed asynchronously
    return {
        "status": "accepted",
        "run_id": result.get("run_id"),
        "articles_created": result.get("articles_created", 0),
    }
