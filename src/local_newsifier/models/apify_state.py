"""State models for Apify ingestion flow."""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from local_newsifier.models.state import ErrorDetails, extract_error_details


class ApifyIngestStatus(str, Enum):
    """Status of the Apify ingestion process."""
    
    INITIALIZED = "INITIALIZED"
    RUNNING_ACTOR = "RUNNING_ACTOR"
    ACTOR_SUCCEEDED = "ACTOR_SUCCEEDED"
    ACTOR_FAILED = "ACTOR_FAILED"
    FETCHING_DATASET = "FETCHING_DATASET"
    DATASET_FETCH_SUCCEEDED = "DATASET_FETCH_SUCCEEDED"
    DATASET_FETCH_FAILED = "DATASET_FETCH_FAILED"
    PROCESSING_ITEMS = "PROCESSING_ITEMS"
    PROCESSING_SUCCEEDED = "PROCESSING_SUCCEEDED"
    PROCESSING_PARTIAL = "PROCESSING_PARTIAL"
    PROCESSING_FAILED = "PROCESSING_FAILED"
    COMPLETED_SUCCESS = "COMPLETED_SUCCESS"
    COMPLETED_WITH_ERRORS = "COMPLETED_WITH_ERRORS"


class ApifyIngestState(BaseModel):
    """State model for the Apify ingestion process."""
    
    run_id: UUID = Field(default_factory=uuid4)
    source_config_id: Optional[int] = None
    actor_id: Optional[str] = None
    actor_input: Dict[str, Any] = Field(default_factory=dict)
    apify_run_id: Optional[str] = None
    dataset_id: Optional[str] = None
    status: ApifyIngestStatus = Field(default=ApifyIngestStatus.INITIALIZED)
    
    # Processing statistics
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    total_items: int = 0
    processed_items: int = 0
    failed_items: int = 0
    skipped_items: int = 0
    
    # Results
    created_article_ids: List[int] = Field(default_factory=list)
    updated_article_ids: List[int] = Field(default_factory=list)
    item_errors: Dict[str, str] = Field(default_factory=dict)
    
    # Error handling
    error_details: Optional[ErrorDetails] = None
    retry_count: int = Field(default=0)
    max_retries: int = Field(default=3)
    
    # Logging
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    run_logs: List[str] = Field(default_factory=list)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "run_id": "123e4567-e89b-12d3-a456-426614174000",
                "source_config_id": 1,
                "actor_id": "apify/web-scraper",
                "actor_input": {"startUrls": [{"url": "https://example.com"}]},
                "status": "INITIALIZED",
                "run_logs": [],
            }
        }
    )
    
    def touch(self) -> None:
        """Update the last_updated timestamp."""
        self.last_updated = datetime.now(timezone.utc)
    
    def add_log(self, message: str) -> None:
        """Add a log message with timestamp."""
        timestamp = datetime.now(timezone.utc).isoformat()
        self.run_logs.append(f"[{timestamp}] {message}")
        self.touch()
    
    def set_error(self, task: str, error: Exception) -> None:
        """Set error details and update status."""
        error_type, message, traceback_snippet = extract_error_details(error)
        self.error_details = ErrorDetails(
            task=task,
            type=error_type,
            message=message,
            traceback_snippet=traceback_snippet,
        )
        # Don't change the status - the caller is responsible for setting the appropriate status
        self.touch()
        
    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate metrics for the ingestion process."""
        duration = None
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
        
        success_rate = 0
        if self.total_items > 0:
            success_rate = (self.processed_items / self.total_items) * 100
        
        return {
            "duration_seconds": duration,
            "total_items": self.total_items,
            "processed_items": self.processed_items,
            "failed_items": self.failed_items,
            "skipped_items": self.skipped_items,
            "success_rate": success_rate,
            "articles_created": len(self.created_article_ids),
            "articles_updated": len(self.updated_article_ids),
        }


class ApifyBatchIngestState(BaseModel):
    """State model for batch Apify ingestion process."""
    
    run_id: UUID = Field(default_factory=uuid4)
    source_config_ids: List[int] = Field(default_factory=list)
    status: ApifyIngestStatus = Field(default=ApifyIngestStatus.INITIALIZED)
    
    # Processing statistics
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    total_configs: int = 0
    processed_configs: int = 0
    failed_configs: int = 0
    
    # Results 
    sub_states: Dict[int, ApifyIngestState] = Field(default_factory=dict)
    
    # Error handling
    error_details: Optional[ErrorDetails] = None
    
    # Logging
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    run_logs: List[str] = Field(default_factory=list)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "run_id": "123e4567-e89b-12d3-a456-426614174000",
                "source_config_ids": [1, 2, 3],
                "status": "INITIALIZED",
                "total_configs": 3,
                "processed_configs": 0,
                "failed_configs": 0,
                "run_logs": [],
            }
        }
    )
    
    def touch(self) -> None:
        """Update the last_updated timestamp."""
        self.last_updated = datetime.now(timezone.utc)
    
    def add_log(self, message: str) -> None:
        """Add a log message with timestamp."""
        timestamp = datetime.now(timezone.utc).isoformat()
        self.run_logs.append(f"[{timestamp}] {message}")
        self.touch()
    
    def set_error(self, task: str, error: Exception) -> None:
        """Set error details and update status."""
        error_type, message, traceback_snippet = extract_error_details(error)
        self.error_details = ErrorDetails(
            task=task,
            type=error_type,
            message=message,
            traceback_snippet=traceback_snippet,
        )
        # Don't change the status - the caller is responsible for setting the appropriate status
        self.touch()
    
    def add_sub_state(self, source_config_id: int, state: ApifyIngestState) -> None:
        """Add a sub-state for a source config."""
        self.sub_states[source_config_id] = state
        self.processed_configs += 1
        if state.status in [
            ApifyIngestStatus.ACTOR_FAILED, 
            ApifyIngestStatus.DATASET_FETCH_FAILED,
            ApifyIngestStatus.PROCESSING_FAILED
        ]:
            self.failed_configs += 1
        self.touch()
        
    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate metrics for the batch ingestion process."""
        duration = None
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
        
        success_rate = 0
        if self.total_configs > 0:
            success_rate = ((self.processed_configs - self.failed_configs) / self.total_configs) * 100
        
        total_items = 0
        processed_items = 0
        failed_items = 0
        skipped_items = 0
        articles_created = 0
        articles_updated = 0
        
        for state in self.sub_states.values():
            total_items += state.total_items
            processed_items += state.processed_items
            failed_items += state.failed_items
            skipped_items += state.skipped_items
            articles_created += len(state.created_article_ids)
            articles_updated += len(state.updated_article_ids)
        
        return {
            "duration_seconds": duration,
            "total_configs": self.total_configs,
            "processed_configs": self.processed_configs,
            "failed_configs": self.failed_configs,
            "success_rate": success_rate,
            "total_items": total_items,
            "processed_items": processed_items,
            "failed_items": failed_items,
            "skipped_items": skipped_items,
            "articles_created": articles_created,
            "articles_updated": articles_updated,
        }