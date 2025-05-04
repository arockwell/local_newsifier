from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class AnalysisStatus(str, Enum):
    """Status of the analysis pipeline."""

    INITIALIZED = "INITIALIZED"
    SCRAPING = "SCRAPING"
    SCRAPE_SUCCEEDED = "SCRAPE_SUCCEEDED"
    SCRAPE_FAILED_NETWORK = "SCRAPE_FAILED_NETWORK"
    SCRAPE_FAILED_PARSING = "SCRAPE_FAILED_PARSING"
    ANALYZING = "ANALYZING"
    ANALYSIS_SUCCEEDED = "ANALYSIS_SUCCEEDED"
    ANALYSIS_FAILED = "ANALYSIS_FAILED"
    SAVING = "SAVING"
    SAVE_SUCCEEDED = "SAVE_SUCCEEDED"
    SAVE_FAILED = "SAVE_FAILED"
    COMPLETED_SUCCESS = "COMPLETED_SUCCESS"
    COMPLETED_WITH_ERRORS = "COMPLETED_WITH_ERRORS"


class TrackingStatus(str, Enum):
    """Status of the entity tracking process."""
    
    INITIALIZED = "INITIALIZED"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class ErrorDetails(BaseModel):
    """Details about an error that occurred during processing."""

    task: str
    type: str
    message: str
    traceback_snippet: Optional[str] = None
    
    
def extract_error_details(error: Exception) -> tuple:
    """Extract error details from an exception, unwrapping ServiceError if needed.
    
    Args:
        error: The exception to extract details from
        
    Returns:
        Tuple of (error_type, message, traceback_snippet)
    """
    # Extract original error message if it's a ServiceError, otherwise use as is
    if hasattr(error, 'original') and error.original:
        # Unwrap the ServiceError to get the original exception
        error_type = error.original.__class__.__name__
        message = str(error.original)
        traceback_snippet = str(error.original.__traceback__)
    else:
        # Use the provided exception as is
        error_type = error.__class__.__name__
        message = str(error)
        traceback_snippet = str(error.__traceback__)
        
    return error_type, message, traceback_snippet


class NewsAnalysisState(BaseModel):
    """State model for the news analysis pipeline."""

    run_id: UUID = Field(default_factory=uuid4)
    target_url: str
    scraped_at: Optional[datetime] = None
    scraped_text: Optional[str] = None
    analyzed_at: Optional[datetime] = None
    analysis_config: Dict[str, List[str]] = Field(
        default_factory=lambda: {"entity_types": ["PERSON", "ORG", "GPE"]}
    )
    analysis_results: Optional[Dict] = None
    saved_at: Optional[datetime] = None
    save_path: Optional[str] = None
    status: AnalysisStatus = Field(default=AnalysisStatus.INITIALIZED)
    error_details: Optional[ErrorDetails] = None
    retry_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    run_logs: List[str] = Field(default_factory=list)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "run_id": "123e4567-e89b-12d3-a456-426614174000",
                "target_url": "https://example.com/news/article",
                "status": "INITIALIZED",
                "analysis_config": {"entity_types": ["PERSON", "ORG", "GPE"]},
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
        self.error_details = ErrorDetails(
            task=task,
            type=error.__class__.__name__,
            message=str(error),
            traceback_snippet=str(error.__traceback__),
        )
        # Don't change the status - the caller is responsible for setting the appropriate status
        self.touch()


class EntityTrackingState(BaseModel):
    """State model for the entity tracking process."""
    
    run_id: UUID = Field(default_factory=uuid4)
    article_id: int
    content: str
    title: str
    published_at: datetime
    entities: List[Dict[str, Any]] = Field(default_factory=list)
    status: TrackingStatus = Field(default=TrackingStatus.INITIALIZED)
    error_details: Optional[ErrorDetails] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    run_logs: List[str] = Field(default_factory=list)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "run_id": "123e4567-e89b-12d3-a456-426614174000",
                "article_id": 1,
                "content": "John Doe visited New York City yesterday.",
                "title": "Local Visit",
                "published_at": "2025-01-01T00:00:00Z",
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
        self.status = TrackingStatus.FAILED
        self.touch()


class EntityBatchTrackingState(BaseModel):
    """State model for batch entity tracking process."""
    
    run_id: UUID = Field(default_factory=uuid4)
    status: TrackingStatus = Field(default=TrackingStatus.INITIALIZED)
    status_filter: str = Field(default="analyzed")
    processed_articles: List[Dict[str, Any]] = Field(default_factory=list)
    total_articles: int = 0
    processed_count: int = 0
    error_count: int = 0
    error_details: Optional[ErrorDetails] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    run_logs: List[str] = Field(default_factory=list)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "run_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "INITIALIZED",
                "status_filter": "analyzed",
                "processed_articles": [],
                "total_articles": 0,
                "processed_count": 0,
                "error_count": 0,
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
        self.status = TrackingStatus.FAILED
        self.touch()
    
    def add_processed_article(self, article_data: Dict[str, Any], success: bool = True) -> None:
        """Add a processed article to the state."""
        self.processed_articles.append(article_data)
        self.processed_count += 1
        if not success:
            self.error_count += 1
        self.touch()


class EntityDashboardState(BaseModel):
    """State model for entity dashboard generation."""
    
    run_id: UUID = Field(default_factory=uuid4)
    status: TrackingStatus = Field(default=TrackingStatus.INITIALIZED)
    days: int = Field(default=30)
    entity_type: str = Field(default="PERSON")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    dashboard_data: Dict[str, Any] = Field(default_factory=dict)
    error_details: Optional[ErrorDetails] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    run_logs: List[str] = Field(default_factory=list)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "run_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "INITIALIZED",
                "days": 30,
                "entity_type": "PERSON",
                "dashboard_data": {},
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
        self.status = TrackingStatus.FAILED
        self.touch()


class EntityRelationshipState(BaseModel):
    """State model for entity relationship analysis."""
    
    run_id: UUID = Field(default_factory=uuid4)
    status: TrackingStatus = Field(default=TrackingStatus.INITIALIZED)
    entity_id: int
    days: int = Field(default=30)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    relationship_data: Dict[str, Any] = Field(default_factory=dict)
    error_details: Optional[ErrorDetails] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    run_logs: List[str] = Field(default_factory=list)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "run_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "INITIALIZED",
                "entity_id": 1,
                "days": 30,
                "relationship_data": {},
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
        self.status = TrackingStatus.FAILED
        self.touch()
