"""Sentiment analysis models for the news analysis system."""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field
from sqlalchemy import (Column, DateTime, Float, ForeignKey, Integer, String, 
                       Table, Text, UniqueConstraint, JSON)
from sqlalchemy.orm import relationship

from .database import Base, ArticleDB


class SentimentAnalysisDB(Base):
    """Database model for article sentiment analysis."""
    
    __tablename__ = "sentiment_analyses"
    
    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    document_sentiment = Column(Float)  # Overall document sentiment score
    document_magnitude = Column(Float)  # Overall document magnitude
    entity_sentiments = Column(JSON)  # Sentiment scores by entity
    topic_sentiments = Column(JSON)  # Sentiment scores by topic
    analyzed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Define a unique constraint
    __table_args__ = (
        UniqueConstraint('article_id', name='uix_sentiment_article'),
    )
    
    # Relationships
    article = relationship("ArticleDB", backref="sentiment_analysis")


class OpinionTrendDB(Base):
    """Database model for tracking sentiment trends over time."""
    
    __tablename__ = "opinion_trends"
    
    id = Column(Integer, primary_key=True)
    topic = Column(String, nullable=False)
    period = Column(String, nullable=False)  # e.g. "2023-01-01"
    period_type = Column(String, nullable=False)  # e.g. "day", "week", "month"
    avg_sentiment = Column(Float)
    sentiment_count = Column(Integer)
    sentiment_distribution = Column(JSON)  # Distribution of sentiment scores
    sources = Column(JSON)  # Sources contributing to this trend
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Define a unique constraint
    __table_args__ = (
        UniqueConstraint('topic', 'period', 'period_type', name='uix_topic_period'),
    )


class SentimentShiftDB(Base):
    """Database model for tracking significant sentiment shifts."""
    
    __tablename__ = "sentiment_shifts"
    
    id = Column(Integer, primary_key=True)
    topic = Column(String, nullable=False)
    start_period = Column(String, nullable=False)
    end_period = Column(String, nullable=False)
    period_type = Column(String, nullable=False)  # e.g. "day", "week", "month"
    start_sentiment = Column(Float)
    end_sentiment = Column(Float)
    shift_magnitude = Column(Float)  # Absolute change
    shift_percentage = Column(Float)  # Percentage change
    supporting_article_ids = Column(JSON)  # List of article IDs supporting this shift
    detected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# Pydantic Models

class SentimentAnalysisBase(BaseModel):
    """Base Pydantic model for sentiment analysis."""
    
    article_id: int
    document_sentiment: float
    document_magnitude: float
    entity_sentiments: Optional[Dict[str, float]] = None
    topic_sentiments: Optional[Dict[str, float]] = None


class SentimentAnalysisCreate(SentimentAnalysisBase):
    """Pydantic model for creating sentiment analysis."""
    
    pass


class SentimentAnalysis(SentimentAnalysisBase):
    """Pydantic model for sentiment analysis with relationships."""
    
    id: int
    analyzed_at: datetime
    
    class Config:
        """Pydantic config."""
        
        from_attributes = True


class OpinionTrendBase(BaseModel):
    """Base Pydantic model for opinion trends."""
    
    topic: str
    period: str
    period_type: str
    avg_sentiment: float
    sentiment_count: int
    sentiment_distribution: Optional[Dict[str, int]] = None
    sources: Optional[Dict[str, int]] = None


class OpinionTrendCreate(OpinionTrendBase):
    """Pydantic model for creating opinion trends."""
    
    pass


class OpinionTrend(OpinionTrendBase):
    """Pydantic model for opinion trends with relationships."""
    
    id: int
    created_at: datetime
    
    class Config:
        """Pydantic config."""
        
        from_attributes = True


class SentimentShiftBase(BaseModel):
    """Base Pydantic model for sentiment shifts."""
    
    topic: str
    start_period: str
    end_period: str
    period_type: str
    start_sentiment: float
    end_sentiment: float
    shift_magnitude: float
    shift_percentage: float
    supporting_article_ids: List[int] = []


class SentimentShiftCreate(SentimentShiftBase):
    """Pydantic model for creating sentiment shifts."""
    
    pass


class SentimentShift(SentimentShiftBase):
    """Pydantic model for sentiment shifts with relationships."""
    
    id: int
    detected_at: datetime
    
    class Config:
        """Pydantic config."""
        
        from_attributes = True


class SentimentVisualizationData(BaseModel):
    """Pydantic model for sentiment visualization data."""
    
    topic: str
    time_periods: List[str]
    sentiment_values: List[float]
    confidence_intervals: Optional[List[Dict[str, float]]] = None
    article_counts: List[int]
    metadata: Optional[Dict[str, Any]] = None