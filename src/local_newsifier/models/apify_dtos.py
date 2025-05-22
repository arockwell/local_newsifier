"""DTOs for Apify service operations."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from .dto_base import BaseListResultDTO, BaseOperationResultDTO


class ApifyDatasetItemDTO(BaseModel):
    """DTO for individual Apify dataset items."""
    
    item_id: str
    data: Dict[str, Any]
    extraction_method: str
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    # Metadata about the extraction
    source_url: Optional[str] = None
    extracted_at: Optional[datetime] = None
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "item_id": "item-123",
                    "data": {
                        "title": "Local News Article",
                        "content": "Article content...",
                        "url": "https://example.com/news/1",
                        "published_date": "2023-01-01"
                    },
                    "extraction_method": "web_scraper",
                    "quality_score": 0.85,
                    "source_url": "https://example.com/news/1",
                    "extracted_at": "2023-01-01T12:00:00Z"
                }
            ]
        }
    }


class ApifyDatasetResponseDTO(BaseListResultDTO[ApifyDatasetItemDTO]):
    """
    Standardized response for Apify dataset operations.
    
    Replaces the complex extraction logic in ApifyService.get_dataset_items()
    with consistent, paginated results and proper error handling.
    """
    
    dataset_id: str
    actor_id: Optional[str] = None
    run_id: Optional[str] = None
    
    # Extraction metadata
    extraction_strategy: str = "auto_detect"
    total_available: Optional[int] = None
    warnings: List[str] = Field(default_factory=list)
    
    # Quality metrics
    average_quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    items_with_errors: int = Field(default=0, ge=0)
    
    def __init__(self, **data):
        super().__init__(**data)
        # Auto-calculate quality metrics
        if self.items:
            quality_scores = [item.quality_score for item in self.items if item.quality_score is not None]
            if quality_scores:
                self.average_quality_score = sum(quality_scores) / len(quality_scores)
            self.items_with_errors = sum(1 for item in self.items if not item.data)
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "items": [
                        {
                            "item_id": "item-123",
                            "data": {"title": "News Article", "content": "..."},
                            "extraction_method": "web_scraper",
                            "quality_score": 0.85
                        }
                    ],
                    "total": 50,
                    "page": 1,
                    "size": 20,
                    "dataset_id": "dataset-456",
                    "actor_id": "news-scraper",
                    "run_id": "run-789",
                    "extraction_strategy": "structured_data",
                    "total_available": 50,
                    "warnings": ["Some items had incomplete data"],
                    "average_quality_score": 0.82,
                    "items_with_errors": 3
                }
            ]
        }
    }


class ApifyActorRunResultDTO(BaseOperationResultDTO):
    """DTO for Apify actor run results."""
    
    run_id: str
    actor_id: str
    status: Literal["READY", "RUNNING", "SUCCEEDED", "FAILED", "TIMED-OUT", "ABORTED"]
    
    # Run metadata
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    runtime_seconds: Optional[float] = None
    
    # Results
    dataset_id: Optional[str] = None
    items_count: Optional[int] = None
    
    # Configuration and costs
    input_parameters: Dict[str, Any] = Field(default_factory=dict)
    memory_mb_used: Optional[int] = None
    compute_units_used: Optional[float] = None
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "status": "completed",
                    "run_id": "run-123",
                    "actor_id": "web-scraper",
                    "status": "SUCCEEDED",
                    "started_at": "2023-01-01T12:00:00Z",
                    "finished_at": "2023-01-01T12:05:00Z",
                    "runtime_seconds": 300.5,
                    "dataset_id": "dataset-456",
                    "items_count": 25,
                    "input_parameters": {"startUrls": ["https://example.com"]},
                    "memory_mb_used": 512,
                    "compute_units_used": 0.05
                }
            ]
        }
    }


class ApifyWebhookEventDTO(BaseModel):
    """DTO for Apify webhook events."""
    
    event_type: str = Field(pattern=r"^[A-Z_]+\.[A-Z_]+$")  # e.g., "ACTOR.RUN.SUCCEEDED"
    event_data: Dict[str, Any]
    created_at: datetime
    
    # Event processing metadata
    processed: bool = False
    processed_at: Optional[datetime] = None
    processing_result: Optional[str] = None
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "event_type": "ACTOR.RUN.SUCCEEDED",
                    "event_data": {
                        "actorId": "web-scraper",
                        "runId": "run-123",
                        "datasetId": "dataset-456"
                    },
                    "created_at": "2023-01-01T12:05:00Z",
                    "processed": True,
                    "processed_at": "2023-01-01T12:05:30Z",
                    "processing_result": "articles_created"
                }
            ]
        }
    }


class ApifyScheduleResultDTO(BaseModel):
    """DTO for Apify schedule operation results."""
    
    schedule_id: str
    actor_id: str
    cron_expression: str
    is_enabled: bool
    
    # Schedule metadata
    next_run_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None
    total_runs: int = Field(default=0, ge=0)
    
    # Recent run statistics
    recent_successful_runs: int = Field(default=0, ge=0)
    recent_failed_runs: int = Field(default=0, ge=0)
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "schedule_id": "schedule-123",
                    "actor_id": "news-scraper",
                    "cron_expression": "0 */6 * * *",
                    "is_enabled": True,
                    "next_run_at": "2023-01-01T18:00:00Z",
                    "last_run_at": "2023-01-01T12:00:00Z",
                    "total_runs": 50,
                    "recent_successful_runs": 8,
                    "recent_failed_runs": 2
                }
            ]
        }
    }


class ApifyConfigurationDTO(BaseModel):
    """DTO for Apify service configuration requests."""
    
    actor_id: str = Field(pattern=r"^[a-zA-Z0-9_.-]+$")
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    
    # Schedule configuration
    schedule_enabled: bool = False
    cron_expression: Optional[str] = Field(None, pattern=r"^(\*|[0-5]?\d)(\s+(\*|[01]?\d|2[0-3])){4}$")
    
    # Processing configuration
    memory_mb: int = Field(default=256, ge=128, le=32768)
    timeout_seconds: int = Field(default=3600, ge=60, le=86400)
    
    # Webhook configuration
    webhook_events: List[str] = Field(default_factory=list)
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "actor_id": "apify/web-scraper",
                    "input_schema": {
                        "startUrls": [{"url": "https://example.com/news"}],
                        "linkSelector": "a[href*='news']",
                        "pageFunction": "// Custom scraping logic"
                    },
                    "schedule_enabled": True,
                    "cron_expression": "0 */6 * * *",
                    "memory_mb": 512,
                    "timeout_seconds": 1800,
                    "webhook_events": ["ACTOR.RUN.SUCCEEDED", "ACTOR.RUN.FAILED"]
                }
            ]
        }
    }