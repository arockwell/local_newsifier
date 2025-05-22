"""
API router for webhook endpoints.

This module provides endpoints for receiving webhook notifications from
external services like Apify, processing the payloads, and triggering
appropriate actions in the system.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from local_newsifier.di.providers import get_apify_webhook_handler
from local_newsifier.models.webhook import ApifyWebhookPayload, ApifyWebhookResponse
from local_newsifier.services.webhook_service import ApifyWebhookHandler

# Create router with /webhooks prefix
router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# Setup logger
logger = logging.getLogger(__name__)


async def process_apify_dataset(
    dataset_id: str,
    job_id: int,
    webhook_handler: ApifyWebhookHandler,
) -> None:
    """Process Apify dataset in the background.

    Args:
        dataset_id: Apify dataset ID to process
        job_id: ApifyJob ID for tracking
        webhook_handler: Handler for webhook processing
    """
    try:
        logger.info(f"Starting background processing of dataset {dataset_id} for job {job_id}")
        success, items_processed, articles_created, error = webhook_handler.process_dataset(
            dataset_id, job_id
        )

        if success:
            logger.info(
                f"Successfully processed dataset {dataset_id}: "
                f"{items_processed} items, {articles_created} articles created"
            )
        else:
            logger.error(f"Failed to process dataset {dataset_id}: {error}")
    except Exception as e:
        logger.exception(f"Error processing dataset {dataset_id}: {str(e)}")


@router.post(
    "/apify",
    response_model=ApifyWebhookResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Receive Apify webhook notifications",
    description="Endpoint for receiving webhook notifications from Apify when runs complete",
)
async def apify_webhook(
    payload: ApifyWebhookPayload,
    background_tasks: BackgroundTasks,
    webhook_handler: Annotated[ApifyWebhookHandler, Depends(get_apify_webhook_handler)],
) -> ApifyWebhookResponse:
    """Handle webhook notifications from Apify.

    Args:
        payload: The webhook payload from Apify
        background_tasks: FastAPI background tasks
        webhook_handler: Handler for webhook processing

    Returns:
        ApifyWebhookResponse: Response acknowledging the webhook

    Raises:
        HTTPException: If webhook validation fails or event type is not supported
    """
    logger.info(f"Received Apify webhook: {payload.eventType} for actor {payload.actorId}")

    # Validate webhook
    if not webhook_handler.validate_webhook(payload):
        logger.warning(f"Invalid webhook: {payload.webhookId} for actor {payload.actorId}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook secret",
        )

    # Handle webhook
    success, job_id, message = webhook_handler.handle_webhook(payload)

    if not success:
        logger.error(f"Error processing webhook: {message}")
        return ApifyWebhookResponse(
            status="error",
            message=message,
            actor_id=payload.actorId,
            dataset_id=payload.defaultDatasetId,
            error="Failed to process webhook",
        )

    # For successful runs, start dataset processing in the background
    if payload.eventType == "ACTOR.RUN.SUCCEEDED" and job_id is not None:
        logger.info(f"Scheduling background processing for dataset {payload.defaultDatasetId}")
        background_tasks.add_task(
            process_apify_dataset,
            dataset_id=payload.defaultDatasetId,
            job_id=job_id,
            webhook_handler=webhook_handler,
        )
        processing_status = "processing_scheduled"
    else:
        processing_status = "webhook_recorded"

    # Return success response
    return ApifyWebhookResponse(
        status="accepted",
        message=message,
        job_id=job_id,
        dataset_id=payload.defaultDatasetId,
        actor_id=payload.actorId,
        processing_status=processing_status,
    )
