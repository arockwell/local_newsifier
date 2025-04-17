"""Sentiment analysis models for the news analysis system using SQLModel."""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from sqlmodel import SQLModel, Field, JSON, UniqueConstraint


class SentimentAnalysis(SQLModel, table=True):
    """SQLModel for article sentiment analysis."""
    
    __tablename__ = "sentiment_analyses"
    
    # Primary key and timestamps
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)}
    )
    
    # Analysis fields
    article_id: Optional[int] = Field(default=None)
    document_sentiment: float
    document_magnitude: float
    entity_sentiments: Optional[Dict[str, float]] = Field(default=None, sa_type=JSON)
    topic_sentiments: Optional[Dict[str, float]] = Field(default=None, sa_type=JSON)
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Define a unique constraint
    __table_args__ = (
        UniqueConstraint("article_id", name="uix_sentiment_article"),
        {"extend_existing": True}
    )


class OpinionTrend(SQLModel, table=True):
    """SQLModel for tracking sentiment trends over time."""
    
    __tablename__ = "opinion_trends"
    
    # Primary key and timestamps
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)}
    )
    
    # Trend fields
    topic: str
    period: str  # e.g. "2023-01-01"
    period_type: str  # e.g. "day", "week", "month"
    avg_sentiment: float
    sentiment_count: int
    sentiment_distribution: Optional[Dict[str, int]] = Field(default=None, sa_type=JSON)
    sources: Optional[Dict[str, int]] = Field(default=None, sa_type=JSON)
    
    # Define a unique constraint
    __table_args__ = (
        UniqueConstraint("topic", "period", "period_type", name="uix_topic_period"),
        {"extend_existing": True}
    )


class SentimentShift(SQLModel, table=True):
    """SQLModel for tracking significant sentiment shifts."""
    
    __tablename__ = "sentiment_shifts"
    
    # Primary key and timestamps
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)}
    )
    
    # Shift fields
    topic: str
    start_period: str
    end_period: str
    period_type: str  # e.g. "day", "week", "month"
    start_sentiment: float
    end_sentiment: float
    shift_magnitude: float  # Absolute change
    shift_percentage: float  # Percentage change
    supporting_article_ids: List[int] = Field(default=[], sa_type=JSON)
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Define table arguments
    __table_args__ = {"extend_existing": True}


# Non-table model for visualization
class SentimentVisualizationData(SQLModel):
    """Model for sentiment visualization data."""
    
    topic: str
    time_periods: List[str]
    sentiment_values: List[float]
    confidence_intervals: Optional[List[Dict[str, float]]] = None
    article_counts: List[int]
    meta_data: Optional[Dict[str, Any]] = None  # Renamed from metadata to avoid conflict