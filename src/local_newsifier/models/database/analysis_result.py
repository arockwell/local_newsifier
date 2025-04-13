"""Analysis result database model for the news analysis system."""

from datetime import datetime, timezone
from typing import Dict, Any, Optional

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, JSON, String
from sqlalchemy.orm import relationship

from local_newsifier.models.database.base import Base


class AnalysisResultBase(BaseModel):
    """Base Pydantic model for analysis results."""
    
    article_id: int
    analysis_type: str
    results: Dict[str, Any]


class AnalysisResultCreate(AnalysisResultBase):
    """Pydantic model for creating analysis results."""
    
    pass


class AnalysisResult(AnalysisResultBase):
    """Pydantic model for analysis results with relationships."""
    
    id: int
    created_at: datetime
    
    class Config:
        """Pydantic config."""
        
        from_attributes = True


class AnalysisResultDB(Base):
    """Database model for analysis results."""
    
    __tablename__ = "analysis_results"
    
    # Foreign key to article
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    
    # Analysis fields
    analysis_type = Column(String, nullable=False)  # e.g., "NER", "sentiment"
    results = Column(JSON, nullable=False)
    
    # Set created_at for backward compatibility (already included from Base)
    
    # Relationships
    article = relationship("ArticleDB", back_populates="analysis_results")
    
    # Indexes
    __table_args__ = (
        Index("ix_analysis_results_type", "analysis_type"),
        Index("ix_analysis_results_article_type", "article_id", "analysis_type"),
    )
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<AnalysisResultDB(id={self.id}, type='{self.analysis_type}')>"
    
    @classmethod
    def from_analysis_result_create(cls, result_data: dict) -> "AnalysisResultDB":
        """Create an AnalysisResultDB instance from analysis result data."""
        return cls(**result_data)