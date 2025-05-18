"""Models for webhook integrations with external systems like Apify."""

from datetime import datetime
from typing import Dict, Any, List, Optional

from pydantic import BaseModel, Field, validator


class ApifyWebhookPayload(BaseModel):
    """Model for Apify webhook payloads.
    
    Represents the webhook notification structure sent by Apify when a run completes.
    Reference: https://docs.apify.com/platform/integrations/webhooks
    """
    
    # Webhook metadata
    createdAt: datetime
    eventType: str  # typically "ACTOR.RUN.SUCCEEDED" for completed runs
    
    # Run information
    actorId: str
    actorRunId: str
    taskId: Optional[str] = None  # May be null if not part of a scheduled task
    buildId: Optional[str] = None
    
    # Standard webhook metadata
    userId: str
    resource: Optional[Dict[str, Any]] = None  # Additional details about the resource
    
    # Content-specific fields
    defaultKeyValueStoreId: str
    defaultDatasetId: str  # This is what we need to retrieve results
    defaultRequestQueueId: Optional[str] = None
    
    # Statistics
    startedAt: datetime
    finishedAt: Optional[datetime] = None
    exitCode: Optional[int] = None
    statusMessage: Optional[str] = None
    
    # Run status
    status: str  # "SUCCEEDED", "FAILED", "ABORTED", etc.
    
    # Webhook configuration
    webhookId: str
    payloadTemplate: Optional[str] = None  # Custom template if used
    
    # Secret validation
    secret: Optional[str] = None  # Used for validating the webhook source


class ApifyWebhookResponse(BaseModel):
    """Response model for Apify webhook endpoint."""
    
    status: str = "accepted"
    message: str
    job_id: Optional[int] = None
    dataset_id: Optional[str] = None
    actor_id: Optional[str] = None
    processing_status: Optional[str] = None
    error: Optional[str] = None


class ApifyDatasetTransformationConfig(BaseModel):
    """Configuration for transforming Apify dataset items to articles."""
    
    # Field mappings
    url_field: str = "url"
    title_field: str = "title"
    content_field: List[str] = Field(default_factory=lambda: ["content", "text"])
    published_at_field: List[str] = Field(
        default_factory=lambda: ["publishedAt", "published_at", "date"]
    )
    source_field: Optional[str] = "source"
    
    # Fallback and processing options
    extract_domain_as_source: bool = True
    force_update_existing: bool = False
    skip_empty_content: bool = True
    min_content_length: int = 100
    
    @validator('content_field', 'published_at_field')
    def ensure_list(cls, v):
        """Ensure these fields are always lists."""
        if isinstance(v, str):
            return [v]
        return v