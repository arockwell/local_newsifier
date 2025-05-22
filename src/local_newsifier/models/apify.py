"""Apify integration models for the Local Newsifier system."""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, TYPE_CHECKING

from sqlmodel import Field, Relationship, JSON, SQLModel

from local_newsifier.models.base import TableBase

# Handle circular imports
if TYPE_CHECKING:
    from local_newsifier.models.article import Article


class ApifySourceConfigBase(TableBase):
    """Base model for ApifySourceConfig."""
    # TODO: move field definitions from ApifySourceConfig here

class ApifySourceConfigRead(ApifySourceConfigBase):
    """Read model for ApifySourceConfig."""
    pass

class ApifyJobBase(TableBase):
    """Base model for ApifyJob."""
    # TODO: move field definitions from ApifyJob here

class ApifyJobRead(ApifyJobBase):
    """Read model for ApifyJob."""
    pass

class ApifyDatasetItemBase(TableBase):
    """Base model for ApifyDatasetItem."""
    # TODO: move field definitions from ApifyDatasetItem here

class ApifyDatasetItemRead(ApifyDatasetItemBase):
    """Read model for ApifyDatasetItem."""
    pass

class ApifyCredentialsBase(TableBase):
    """Base model for ApifyCredentials."""
    # TODO: move field definitions from ApifyCredentials here

class ApifyCredentialsRead(ApifyCredentialsBase):
    """Read model for ApifyCredentials."""
    pass

class ApifyWebhookBase(TableBase):
    """Base model for ApifyWebhook."""
    # TODO: move field definitions from ApifyWebhook here

class ApifyWebhookRead(ApifyWebhookBase):
    """Read model for ApifyWebhook."""
    pass

class ApifySourceConfig(ApifySourceConfigBase, table=True):
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


class ApifyJob(ApifyJobBase, table=True):
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


class ApifyDatasetItem(ApifyDatasetItemBase, table=True):
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


class ApifyCredentials(ApifyCredentialsBase, table=True):
    """SQLModel for storing Apify API credentials."""

    __tablename__ = "apify_credentials"
    
    # Handle multiple imports during test collection
    __table_args__ = {"extend_existing": True}

    api_token: str  # Encrypted API token
    label: str = Field(index=True)  # Descriptive label for this token
    is_active: bool = Field(default=True)
    rate_limit_remaining: Optional[int] = None  # For tracking API usage


class ApifyWebhook(ApifyWebhookBase, table=True):
    """SQLModel for managing Apify webhooks."""

    __tablename__ = "apify_webhooks"
    
    # Handle multiple imports during test collection
    __table_args__ = {"extend_existing": True}

    webhook_id: str = Field(index=True)  # Apify webhook ID
    actor_id: Optional[str] = None  # Actor this webhook is associated with (if any)
    event_types: List[str] = Field(default_factory=list, sa_type=JSON)  # e.g., ["RUN.SUCCEEDED"]
    payload_template: Optional[str] = None  # Custom payload template if used
    is_active: bool = Field(default=True)
