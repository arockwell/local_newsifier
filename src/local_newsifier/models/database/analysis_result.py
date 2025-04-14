"""Analysis result models for the news analysis system."""

from datetime import datetime
from typing import Dict, Any

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, JSON
from sqlalchemy.orm import relationship

from local_newsifier.models.database.base import Base


class AnalysisResultDB(Base):
    """Database model for analysis results."""

    __tablename__ = "analysis_results"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    analysis_type = Column(String, nullable=False)
    results = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now())

    # Relationships
    article = relationship("ArticleDB", back_populates="analysis_results")