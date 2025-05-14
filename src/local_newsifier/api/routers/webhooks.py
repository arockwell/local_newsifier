"""Webhook endpoints for Local Newsifier."""

import hmac
import logging
from typing import Annotated, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from fastapi_injectable import injectable
from pydantic import BaseModel, Field

from local_newsifier.config.settings import settings
from local_newsifier.di.providers import get_apify_webhook_handler
from sqlmodel import Session

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)


class ApifyWebhookPayload(BaseModel):
    """Model for Apify webhook payload.
    
    Based on Apify webhook documentation: https://docs.apify.com/platform/integrations/webhooks/actions
    """
    # Required fields
    createdAt: str
    eventType: str = Field(..., alias="event_type")
    userId: str
    webhookId: str = Field(..., alias="webhook_id")
    
    # Optional fields depending on event type
    actorId: Optional[str] = Field(None, alias="actor_id")
    actorRunId: Optional[str] = Field(None, alias="actor_run_id")
    actorTaskId: Optional[str] = None
    resource: Optional[Dict[str, Any]] = None
    datasetId: Optional[str] = Field(None, alias="dataset_id")
    defaultDatasetId: Optional[str] = None
    defaultKeyValueStoreId: Optional[str] = None
    
    class Config:
        populate_by_name = True
        extra = "allow"  # Allow additional fields in the payload


@router.post("/apify", status_code=status.HTTP_202_ACCEPTED)
async def apify_webhook(
    payload: ApifyWebhookPayload,
    request: Request,
    apify_webhook_handler: Annotated[Any, Depends(get_apify_webhook_handler)],
    x_apify_webhook_secret: Optional[str] = Header(None)
):
    """Handle Apify webhook calls.
    
    This endpoint receives notifications when Apify scraping jobs complete
    and processes the resulting datasets to create articles.
    
    Args:
        payload: The webhook payload from Apify
        request: The FastAPI request object
        x_apify_webhook_secret: Secret token for webhook verification
        apify_service: Service for Apify API operations
        article_service: Service for article operations
        session: Database session
        
    Returns:
        Confirmation message
    """
    # Validate the webhook secret if configured
    if settings.APIFY_WEBHOOK_SECRET:
        if not x_apify_webhook_secret:
            logger.warning("Webhook secret validation failed: Missing x-apify-webhook-secret header")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing webhook secret header"
            )
        
        if not hmac.compare_digest(settings.APIFY_WEBHOOK_SECRET, x_apify_webhook_secret):
            logger.warning("Webhook secret validation failed: Invalid webhook secret")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook secret"
            )
    
    # Log the webhook call
    logger.info(f"Received Apify webhook: {payload.eventType} for webhook {payload.webhookId}")
    
    # Only process RUN.SUCCEEDED events with dataset_id
    if payload.eventType != "RUN.SUCCEEDED" or not payload.datasetId:
        logger.info(f"Ignoring webhook for eventType={payload.eventType}, datasetId={payload.datasetId}")
        return {"status": "accepted", "message": "Event not processed: not a successful run with dataset"}
    
    # Process webhook asynchronously
    # Use create_task to run in background without awaiting completion
    import asyncio
    webhook_data = payload.model_dump(by_alias=True)
    asyncio.create_task(apify_webhook_handler.process_webhook(webhook_data))
    
    # Return immediate acceptance
    return {"status": "accepted", "message": "Webhook received successfully"}