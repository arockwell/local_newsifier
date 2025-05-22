"""Apify integration models for the Local Newsifier system."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlmodel import JSON, Field, Relationship, SQLModel

from local_newsifier.models.base import TableBase

# Handle circular imports
if TYPE_CHECKING:
    from local_newsifier.models.article import Article


class ApifySourceConfig(TableBase, table=True):
    """SQLModel for storing Apify scraper configurations."""

    __tablename__ = "apify_source_configs"
    
    # Handle multiple imports during test collection
    __table_args__ = {"extend_existing": True}

    name: str = Field(index=True)  # Human-readable name for this source
    actor_id: str  # Apify actor ID
    is_active: bool = Field(default=True)
    schedule: Optional[str] = None  # Cron expression for scheduling
    schedule_id: Optional[str] = None  # ID of the created Apify schedule
    source_type: str  # e.g., "news", "blog", "social_media"
    source_url: Optional[str] = None  # Original source URL if applicable

    # Configuration parameters for the actor
    input_configuration: Dict[str, Any] = Field(default_factory=dict, sa_type=JSON)

    # Metadata and timestamps
    last_run_at: Optional[datetime] = None

    # Relationships
    jobs: List["ApifyJob"] = Relationship(back_populates="source_config")


class ApifyJob(TableBase, table=True):
    """SQLModel for tracking Apify job runs."""

    __tablename__ = "apify_jobs"
    
    # Handle multiple imports during test collection
    __table_args__ = {"extend_existing": True}

    source_config_id: Optional[int] = Field(default=None, foreign_key="apify_source_configs.id", index=True)
    run_id: str = Field(index=True)  # Apify run ID
    actor_id: str  # Apify actor ID that was run
    status: str  # e.g., "RUNNING", "SUCCEEDED", "FAILED", "ABORTED"

    # Run statistics
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None

    # Results metadata
    dataset_id: Optional[str] = None  # Apify dataset ID with results
    item_count: Optional[int] = None  # Number of items scraped
    error_message: Optional[str] = None

    # Processing status
    processed: bool = Field(default=False)  # Whether results were imported to articles
    articles_created: Optional[int] = None  # Number of articles created from this job
    processed_at: Optional[datetime] = None

    # Relationship back to source config
    source_config: Optional["ApifySourceConfig"] = Relationship(back_populates="jobs")
    
    # Relationship to dataset items
    dataset_items: List["ApifyDatasetItem"] = Relationship(back_populates="job")


class ApifyDatasetItem(TableBase, table=True):
    """SQLModel for storing raw Apify dataset items before transformation."""

    __tablename__ = "apify_dataset_items"
    
    # Handle multiple imports during test collection
    __table_args__ = {"extend_existing": True}

    job_id: int = Field(foreign_key="apify_jobs.id", index=True)
    apify_id: str  # Original item ID from Apify
    raw_data: Dict[str, Any] = Field(sa_type=JSON)

    # Processing status
    transformed: bool = Field(default=False)
    article_id: Optional[int] = Field(default=None, foreign_key="articles.id", index=True)
    error_message: Optional[str] = None

    # Relationships
    job: "ApifyJob" = Relationship(back_populates="dataset_items")
    article: Optional["local_newsifier.models.article.Article"] = Relationship()


class ApifyCredentials(TableBase, table=True):
    """SQLModel for storing Apify API credentials."""

    __tablename__ = "apify_credentials"
    
    # Handle multiple imports during test collection
    __table_args__ = {"extend_existing": True}

    api_token: str  # Encrypted API token
    label: str = Field(index=True)  # Descriptive label for this token
    is_active: bool = Field(default=True)
    rate_limit_remaining: Optional[int] = None  # For tracking API usage


class ApifyWebhook(TableBase, table=True):
    """SQLModel for managing Apify webhooks."""

    __tablename__ = "apify_webhooks"
    
    # Handle multiple imports during test collection
    __table_args__ = {"extend_existing": True}

    webhook_id: str = Field(index=True)  # Apify webhook ID
    actor_id: Optional[str] = None  # Actor this webhook is associated with (if any)
    event_types: List[str] = Field(default_factory=list, sa_type=JSON)  # e.g., ["RUN.SUCCEEDED"]
    payload_template: Optional[str] = None  # Custom payload template if used
    is_active: bool = Field(default=True)


# Read DTOs for API responses
class ApifySourceConfigRead(SQLModel):
    """Read DTO for ApifySourceConfig model - used for API responses."""
    
    id: int
    created_at: datetime
    updated_at: datetime
    name: str
    actor_id: str
    is_active: bool
    schedule: Optional[str] = None
    schedule_id: Optional[str] = None
    source_type: str
    source_url: Optional[str] = None
    input_configuration: Dict[str, Any]
    last_run_at: Optional[datetime] = None
    
    # Related job IDs instead of full objects
    job_ids: List[int] = Field(default_factory=list)
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "name": "Local News Scraper",
                    "actor_id": "news-scraper-actor",
                    "is_active": True,
                    "schedule": "0 */6 * * *",
                    "source_type": "news",
                    "source_url": "https://example.com",
                    "input_configuration": {"url": "https://example.com/news"},
                    "job_ids": [1, 2, 3]
                }
            ]
        }
    }


class ApifyJobRead(SQLModel):
    """Read DTO for ApifyJob model - used for API responses."""
    
    id: int
    created_at: datetime
    updated_at: datetime
    source_config_id: Optional[int] = None
    run_id: str
    actor_id: str
    status: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    dataset_id: Optional[str] = None
    item_count: Optional[int] = None
    error_message: Optional[str] = None
    processed: bool
    articles_created: Optional[int] = None
    processed_at: Optional[datetime] = None
    
    # Related dataset item IDs instead of full objects
    dataset_item_ids: List[int] = Field(default_factory=list)
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "source_config_id": 1,
                    "run_id": "apify-run-123",
                    "actor_id": "news-scraper-actor",
                    "status": "SUCCEEDED",
                    "started_at": "2023-01-01T12:00:00Z",
                    "finished_at": "2023-01-01T12:05:00Z",
                    "duration_seconds": 300,
                    "item_count": 10,
                    "processed": True,
                    "articles_created": 5,
                    "dataset_item_ids": [1, 2, 3]
                }
            ]
        }
    }


class ApifyDatasetItemRead(SQLModel):
    """Read DTO for ApifyDatasetItem model - used for API responses."""
    
    id: int
    created_at: datetime
    updated_at: datetime
    job_id: int
    apify_id: str
    raw_data: Dict[str, Any]
    transformed: bool
    article_id: Optional[int] = None
    error_message: Optional[str] = None
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "job_id": 1,
                    "apify_id": "item-123",
                    "raw_data": {
                        "title": "Breaking News",
                        "content": "News content...",
                        "url": "https://example.com/news/1"
                    },
                    "transformed": True,
                    "article_id": 1
                }
            ]
        }
    }


class ApifyCredentialsRead(SQLModel):
    """Read DTO for ApifyCredentials model - used for API responses."""
    
    id: int
    created_at: datetime
    updated_at: datetime
    # Note: api_token is intentionally excluded for security
    label: str
    is_active: bool
    rate_limit_remaining: Optional[int] = None
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "label": "Production Token",
                    "is_active": True,
                    "rate_limit_remaining": 1000
                }
            ]
        }
    }


class ApifyWebhookRead(SQLModel):
    """Read DTO for ApifyWebhook model - used for API responses."""
    
    id: int
    created_at: datetime
    updated_at: datetime
    webhook_id: str
    actor_id: Optional[str] = None
    event_types: List[str]
    payload_template: Optional[str] = None
    is_active: bool
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "webhook_id": "webhook-123",
                    "actor_id": "news-scraper-actor",
                    "event_types": ["RUN.SUCCEEDED", "RUN.FAILED"],
                    "is_active": True
                }
            ]
        }
    }
