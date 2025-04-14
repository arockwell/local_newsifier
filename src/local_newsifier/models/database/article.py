"""Article models for the news analysis system."""

from datetime import datetime
from typing import List

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship

from local_newsifier.models.database.base import Base
from local_newsifier.models.database.analysis_result import AnalysisResultDB

class ArticleDB(Base):
    """Database model for articles."""

    __tablename__ = "articles"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    url = Column(String(512), nullable=False, unique=True)
    source = Column(String(255), nullable=False)
    published_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String(50), nullable=False)
    scraped_at = Column(DateTime, nullable=False)

    # Define relationships
    entities = relationship("EntityDB", back_populates="article")
    analysis_results = relationship("AnalysisResultDB", back_populates="article")