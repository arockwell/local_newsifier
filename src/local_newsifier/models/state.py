from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import ConfigDict, Field

from .base_state import BaseState, ErrorDetails, extract_error_details


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




class NewsAnalysisState(BaseState):
    """State model for the news analysis pipeline."""

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
    retry_count: int = Field(default=0)

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



class EntityTrackingState(BaseState):
    """State model for the entity tracking process."""
    
    article_id: int
    content: str
    title: str
    published_at: datetime
    entities: List[Dict[str, Any]] = Field(default_factory=list)
    status: TrackingStatus = Field(default=TrackingStatus.INITIALIZED)
    failure_status: TrackingStatus = TrackingStatus.FAILED
    
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
    


class EntityBatchTrackingState(BaseState):
    """State model for batch entity tracking process."""
    
    status: TrackingStatus = Field(default=TrackingStatus.INITIALIZED)
    failure_status: TrackingStatus = TrackingStatus.FAILED
    status_filter: str = Field(default="analyzed")
    processed_articles: List[Dict[str, Any]] = Field(default_factory=list)
    total_articles: int = 0
    processed_count: int = 0
    error_count: int = 0
    error_details: Optional[ErrorDetails] = None
    
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
    
    
    def add_processed_article(self, article_data: Dict[str, Any], success: bool = True) -> None:
        """Add a processed article to the state."""
        self.processed_articles.append(article_data)
        self.processed_count += 1
        if not success:
            self.error_count += 1
        self.touch()


class EntityDashboardState(BaseState):
    """State model for entity dashboard generation."""
    
    status: TrackingStatus = Field(default=TrackingStatus.INITIALIZED)
    failure_status: TrackingStatus = TrackingStatus.FAILED
    days: int = Field(default=30)
    entity_type: str = Field(default="PERSON")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    dashboard_data: Dict[str, Any] = Field(default_factory=dict)
    error_details: Optional[ErrorDetails] = None
    
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
    


class EntityRelationshipState(BaseState):
    """State model for entity relationship analysis."""
    
    status: TrackingStatus = Field(default=TrackingStatus.INITIALIZED)
    failure_status: TrackingStatus = TrackingStatus.FAILED
    entity_id: int
    days: int = Field(default=30)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    relationship_data: Dict[str, Any] = Field(default_factory=dict)
    error_details: Optional[ErrorDetails] = None
    
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
    
