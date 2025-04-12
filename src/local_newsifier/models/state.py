from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional
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


class ErrorDetails(BaseModel):
    """Details about an error that occurred during processing."""
    task: str
    type: str
    message: str
    traceback_snippet: Optional[str] = None


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
                "run_logs": []
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
            traceback_snippet=str(error.__traceback__)
        )
        self.touch() 