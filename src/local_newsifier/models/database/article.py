"""Article models for the news analysis system."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship

from local_newsifier.models.database.base import Base


class ArticleDB(Base):
    """Database model for articles."""

    __tablename__ = "articles"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, nullable=False)
    title = Column(String)
    source = Column(String)
    published_at = Column(DateTime)
    content = Column(Text)
    status = Column(String)
    scraped_at = Column(DateTime, default=lambda: datetime.now())

    # Relationships
    entities = relationship("local_newsifier.models.database.entity.EntityDB", back_populates="article")
    analysis_results = relationship("local_newsifier.models.database.analysis_result.AnalysisResultDB", back_populates="article")


class ArticleBase(BaseModel):
    """Base Pydantic model for articles."""

    url: str
    title: Optional[str] = None
    source: Optional[str] = None
    published_at: Optional[datetime] = None
    content: Optional[str] = None
    status: Optional[str] = None


class ArticleCreate(ArticleBase):
    """Pydantic model for creating articles."""

    pass


class Article(ArticleBase):
    """Pydantic model for articles with relationships."""

    id: int
    scraped_at: datetime
    entities: List["Entity"] = []
    analysis_results: List["AnalysisResult"] = []

    class Config:
        """Pydantic config."""

        from_attributes = True


# Import related models after defining Article to avoid circular imports
from local_newsifier.models.database.entity import Entity
from local_newsifier.models.database.analysis_result import AnalysisResult

# Update forward references
Article.model_rebuild()