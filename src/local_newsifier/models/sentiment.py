"""Sentiment analysis models for the news analysis system using SQLModel."""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from sqlmodel import SQLModel, Field, Relationship, JSON

from local_newsifier.models.database.base import TableBase


class SentimentAnalysis(TableBase, table=True):
    """SQLModel for article sentiment analysis."""
    
    __tablename__ = "sentiment_analyses"
    
    article_id: int = Field(foreign_key="articles.id")
    document_sentiment: float
    document_magnitude: float
    entity_sentiments: Optional[Dict[str, float]] = Field(default=None, sa_type=JSON)
    topic_sentiments: Optional[Dict[str, float]] = Field(default=None, sa_type=JSON)
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Define a unique constraint
    __table_args__ = (
        {"UniqueConstraint": ("article_id", "name", "uix_sentiment_article")},
        {"extend_existing": True}
    )
    
    # Relationships will be defined with Link models later


class OpinionTrend(TableBase, table=True):
    """SQLModel for tracking sentiment trends over time."""
    
    __tablename__ = "opinion_trends"
    
    topic: str
    period: str  # e.g. "2023-01-01"
    period_type: str  # e.g. "day", "week", "month"
    avg_sentiment: float
    sentiment_count: int
    sentiment_distribution: Optional[Dict[str, int]] = Field(default=None, sa_type=JSON)
    sources: Optional[Dict[str, int]] = Field(default=None, sa_type=JSON)
    
    # Define a unique constraint
    __table_args__ = (
        {"UniqueConstraint": ("topic", "period", "period_type", "name", "uix_topic_period")},
        {"extend_existing": True}
    )


class SentimentShift(TableBase, table=True):
    """SQLModel for tracking significant sentiment shifts."""
    
    __tablename__ = "sentiment_shifts"
    
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


# Visualization model (not a database table)
class SentimentVisualizationData(SQLModel):
    """Model for sentiment visualization data."""
    
    topic: str
    time_periods: List[str]
    sentiment_values: List[float]
    confidence_intervals: Optional[List[Dict[str, float]]] = None
    article_counts: List[int]
    metadata: Optional[Dict[str, Any]] = None