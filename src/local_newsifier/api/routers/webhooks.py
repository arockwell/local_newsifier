"""
API router for webhook endpoints.

This module provides endpoints for receiving webhook notifications from
external services like Apify, validating payloads, and processing data.
"""

import json
import logging
from typing import Annotated, Any, Dict

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Request
from fastapi import status as http_status

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
    status_code=http_status.HTTP_202_ACCEPTED,
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
        # Extract key fields for logging
        event_data = payload.get("eventData", {})
        resource = payload.get("resource", {})
        run_id = event_data.get("actorRunId", "") or resource.get("id", "")
        actor_id = event_data.get("actorId", "") or resource.get("actId", "")
        status = resource.get("status", "")

        # Log incoming webhook
        logger.info(f"Webhook received: run_id={run_id}, actor_id={actor_id}, status={status}")

        # Log signature validation attempt
        if apify_webhook_signature:
            logger.info(f"Signature validation: attempting validation for run_id={run_id}")
        else:
            logger.debug(f"Signature validation: no signature provided for run_id={run_id}")

        # Log request headers for debugging (sanitized)
        headers_dict = dict(request.headers)
        # Remove sensitive headers
        safe_headers = {
            k: v
            for k, v in headers_dict.items()
            if k.lower() not in ["authorization", "x-api-key", "cookie"]
        }
        logger.debug(f"Request headers: {safe_headers}")

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
            logger.error(f"Webhook processing error: run_id={run_id}, error={result['message']}")
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST, detail=result["message"]
            )

        # Log successful response
        articles_created = result.get("articles_created", 0)
        logger.info(
            f"Webhook response: run_id={run_id}, status=accepted, "
            f"articles_created={articles_created}"
        )

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
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        # Include run_id in error response if available
        run_id = "unknown"
        try:
            event_data = payload.get("eventData", {})
            resource = payload.get("resource", {})
            run_id = event_data.get("actorRunId", "") or resource.get("id", "") or "unknown"
        except Exception:
            pass

        logger.error(f"Webhook processing failed: run_id={run_id}, error={str(e)}")
        logger.debug(f"Webhook payload on error: {payload}")
        return ApifyWebhookResponse(
            status="error", message=f"Error processing webhook: {str(e)}", error=str(e)
        )
