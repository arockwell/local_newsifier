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
from local_newsifier.services.apify_webhook_service import ApifyWebhookService

# Create router with /webhooks prefix
router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# Setup logger
logger = logging.getLogger(__name__)


def get_webhook_service(session: Annotated[Session, Depends(get_session)]) -> ApifyWebhookService:
    """Get webhook service instance."""
    settings = get_settings()
    webhook_secret = settings.APIFY_WEBHOOK_SECRET
    return ApifyWebhookService(session=session, webhook_secret=webhook_secret)


@router.post(
    "/apify",
    status_code=http_status.HTTP_202_ACCEPTED,
    summary="Receive Apify webhook notifications",
    description="Simple endpoint that accepts Apify webhooks and processes them idempotently",
)
def apify_webhook(
    request: Request,
    payload: Annotated[Dict[str, Any], Body()],
    webhook_service: Annotated[ApifyWebhookService, Depends(get_webhook_service)],
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

    from fastapi import HTTPException

    raw_payload = json.dumps(payload, separators=(",", ":"), sort_keys=True)

    # EMERGENCY LOGGING: Log full payload structure for debugging
    # TODO: Make this configurable via environment variable once webhook is stable
    logger.info("=== WEBHOOK RECEIVED ===")
    logger.info(f"Payload keys: {list(payload.keys())}")
    logger.info(f"Full payload: {json.dumps(payload, indent=2)}")

    # Extract key fields for logging
    event_data = payload.get("eventData", {})
    resource = payload.get("resource", {})
    run_id = event_data.get("actorRunId", "") or resource.get("id", "")
    actor_id = event_data.get("actorId", "") or resource.get("actId", "")
    status = resource.get("status", "")

    # Log incoming webhook
    logger.info(f"Webhook received: run_id={run_id}, actor_id={actor_id}, status={status}")

    try:
        # Process webhook
        result = webhook_service.handle_webhook(
            payload=payload,
            raw_payload=raw_payload,
            signature=apify_webhook_signature,
        )
    except ValueError as e:
        # Return 400 Bad Request for validation errors
        # This tells Apify not to retry invalid requests
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        # Log unexpected errors but still accept the webhook
        # This allows for retries and prevents webhook queue blocking
        logger.error(f"Unexpected error handling webhook: {e}")
        logger.error(f"Error occurred with payload: {json.dumps(payload, indent=2)}")
        # Extract IDs from payload (support both formats)
        resource = payload.get("resource", {})
        if resource:
            run_id = resource.get("id")
            actor_id = resource.get("actId")
            dataset_id = resource.get("defaultDatasetId")
        else:
            run_id = payload.get("actorRunId")
            actor_id = payload.get("actorId")
            dataset_id = payload.get("defaultDatasetId")

        return {
            "status": "error",
            "message": str(e),
            "run_id": run_id,
            "actor_id": actor_id,
            "dataset_id": dataset_id,
            "processing_status": "error",
            "articles_created": 0,
        }

    # Return error status if validation failed
    if result["status"] == "error":
        # Return 400 Bad Request for invalid webhooks
        # This tells Apify not to retry invalid requests
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=result["message"])

    # Return simple success response
    # 202 Accepted is appropriate for webhooks that are processed asynchronously
    return {
        "status": "accepted",
        "run_id": result.get("run_id"),
        "articles_created": result.get("articles_created", 0),
        "actor_id": result.get("actor_id"),
        "dataset_id": result.get("dataset_id"),
        "processing_status": "completed" if result["status"] == "ok" else "error",
        "message": result.get("message", "Webhook processed"),
    }


@router.get(
    "/apify/debug/{dataset_id}",
    status_code=http_status.HTTP_200_OK,
    summary="Debug Apify dataset download",
    description="Analyze dataset contents and article creation process for debugging",
)
def debug_apify_dataset(
    dataset_id: str,
    webhook_service: Annotated[ApifyWebhookService, Depends(get_webhook_service)],
) -> Dict[str, Any]:
    """Debug endpoint to analyze Apify dataset download issues.

    This endpoint:
    1. Fetches the dataset from Apify
    2. Analyzes each item for required fields
    3. Checks for existing articles by URL
    4. Reports why articles were/weren't created

    Args:
        dataset_id: Apify dataset ID to analyze
        webhook_service: Injected webhook service

    Returns:
        Detailed analysis of dataset items and article creation
    """
    from fastapi import HTTPException

    from local_newsifier.crud.article import article

    try:
        # Get the Apify service from webhook service
        apify_service = webhook_service.apify_service

        # Fetch dataset items
        logger.info(f"Debug: Fetching dataset {dataset_id}")
        try:
            dataset_items = apify_service.client.dataset(dataset_id).list_items().items
        except Exception as e:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Dataset not found or inaccessible: {str(e)}",
            )

        # Analyze each item
        analysis = {
            "dataset_id": dataset_id,
            "total_items": len(dataset_items),
            "items_analysis": [],
            "summary": {
                "valid_items": 0,
                "missing_url": 0,
                "missing_title": 0,
                "missing_content": 0,
                "content_too_short": 0,
                "duplicate_articles": 0,
                "creatable_articles": 0,
            },
        }

        session = webhook_service.session

        for idx, item in enumerate(dataset_items):
            # Extract fields
            url = item.get("url", "")
            title = item.get("title", "")
            content = (
                item.get("content", "")
                or item.get("text", "")
                or item.get("body", "")
                or item.get("description", "")
            )

            # Analyze item
            item_analysis = {
                "index": idx,
                "url": url[:100] + "..." if len(url) > 100 else url,
                "has_url": bool(url),
                "has_title": bool(title),
                "title_preview": title[:50] + "..." if len(title) > 50 else title,
                "content_fields": [
                    k for k in ["content", "text", "body", "description"] if k in item
                ],
                "content_length": len(content),
                "content_preview": content[:100] + "..." if content else "",
                "issues": [],
                "would_create_article": False,
            }

            # Check for issues
            if not url:
                item_analysis["issues"].append("Missing URL")
                analysis["summary"]["missing_url"] += 1
            if not title:
                item_analysis["issues"].append("Missing title")
                analysis["summary"]["missing_title"] += 1
            if not content:
                item_analysis["issues"].append("No content found in any field")
                analysis["summary"]["missing_content"] += 1
            elif len(content) < 100:
                item_analysis["issues"].append(f"Content too short ({len(content)} chars < 100)")
                analysis["summary"]["content_too_short"] += 1

            # Check if article exists
            if url:
                existing_article = article.get_by_url(session, url=url)
                if existing_article:
                    item_analysis["issues"].append(
                        f"Article already exists (ID: {existing_article.id})"
                    )
                    analysis["summary"]["duplicate_articles"] += 1

            # Determine if article would be created
            if url and title and len(content) >= 100 and not existing_article:
                item_analysis["would_create_article"] = True
                analysis["summary"]["creatable_articles"] += 1
                analysis["summary"]["valid_items"] += 1
            elif not item_analysis["issues"]:
                analysis["summary"]["valid_items"] += 1

            analysis["items_analysis"].append(item_analysis)

        # Add recommendations
        analysis["recommendations"] = []
        if analysis["summary"]["missing_content"] > 0:
            analysis["recommendations"].append(
                "Some items have no content. Check if the actor is configured to "
                "extract article content."
            )
        if analysis["summary"]["content_too_short"] > 0:
            analysis["recommendations"].append(
                "Some items have very short content. The actor may need to extract "
                "full article text."
            )
        if analysis["summary"]["missing_url"] > 0:
            analysis["recommendations"].append(
                "Some items are missing URLs. Ensure the actor outputs a 'url' field."
            )
        if analysis["summary"]["creatable_articles"] == 0:
            analysis["recommendations"].append(
                "No articles can be created from this dataset. Check the actor " "configuration."
            )

        return analysis

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error debugging dataset {dataset_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing dataset: {str(e)}",
        )
