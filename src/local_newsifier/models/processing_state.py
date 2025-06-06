"""Generic processing state model to replace multiple specific state models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import ConfigDict, Field

from .base_state import BaseState


class ProcessingStatus(str, Enum):
    """Generic status for any processing operation."""

    # Common states
    INITIALIZED = "INITIALIZED"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

    # Additional states for complex workflows
    SCRAPING = "SCRAPING"
    SCRAPE_SUCCEEDED = "SCRAPE_SUCCEEDED"
    SCRAPE_FAILED = "SCRAPE_FAILED"
    ANALYZING = "ANALYZING"
    ANALYSIS_SUCCEEDED = "ANALYSIS_SUCCEEDED"
    ANALYSIS_FAILED = "ANALYSIS_FAILED"
    SAVING = "SAVING"
    SAVE_SUCCEEDED = "SAVE_SUCCEEDED"
    SAVE_FAILED = "SAVE_FAILED"
    COMPLETED_SUCCESS = "COMPLETED_SUCCESS"
    COMPLETED_WITH_ERRORS = "COMPLETED_WITH_ERRORS"


class ProcessingState(BaseState):
    """Generic state model for any processing operation.

    This model replaces specific state models like:
    - NewsAnalysisState
    - EntityTrackingState
    - EntityBatchTrackingState
    - EntityDashboardState
    - EntityRelationshipState

    Use the processing_type field to distinguish between different operations.
    """

    # Required fields
    processing_type: str  # e.g., "news_analysis", "entity_tracking", "entity_dashboard"
    status: ProcessingStatus = Field(default=ProcessingStatus.INITIALIZED)

    # Generic data storage
    data: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)

    # Common optional fields
    target_id: Optional[int] = None  # article_id, entity_id, etc.
    target_url: Optional[str] = None

    # Processing metadata
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Counters for batch operations
    total_items: int = 0
    processed_items: int = 0
    error_count: int = 0

    # Set failure status for automatic error handling
    failure_status: ProcessingStatus = ProcessingStatus.FAILED

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "run_id": "123e4567-e89b-12d3-a456-426614174000",
                "processing_type": "entity_tracking",
                "status": "INITIALIZED",
                "data": {},
                "errors": [],
                "run_logs": [],
            }
        }
    )

    def start_processing(self) -> None:
        """Mark the start of processing."""
        self.status = ProcessingStatus.PROCESSING
        self.started_at = datetime.utcnow()
        self.add_log(f"Started {self.processing_type} processing")

    def complete_processing(self, success: bool = True) -> None:
        """Mark the completion of processing."""
        self.completed_at = datetime.utcnow()
        if success:
            self.status = ProcessingStatus.SUCCESS
            self.add_log(f"Completed {self.processing_type} processing successfully")
        else:
            self.status = ProcessingStatus.FAILED
            self.add_log(f"Failed {self.processing_type} processing")

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
        self.error_count += 1
        self.add_log(f"Error: {error}")

    def increment_processed(self, success: bool = True) -> None:
        """Increment processed counter."""
        self.processed_items += 1
        if not success:
            self.error_count += 1

    def set_data(self, key: str, value: Any) -> None:
        """Set a data value."""
        self.data[key] = value
        self.touch()

    def get_data(self, key: str, default: Any = None) -> Any:
        """Get a data value."""
        return self.data.get(key, default)
