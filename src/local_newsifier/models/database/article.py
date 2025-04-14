"""Article models for the news analysis system."""

from datetime import UTC, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, relationship

from local_newsifier.models.database.base import Base
from local_newsifier.models.state import AnalysisStatus


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


class ArticleBase(BaseModel):
    """Base Pydantic model for articles."""

    url: str
    title: Optional[str] = None
    source: Optional[str] = None
    published_at: Optional[datetime] = None
    content: Optional[str] = None
    status: Optional[str] = None


class ArticleCreate(BaseModel):
    """Pydantic model for article creation."""
    title: str
    content: str
    url: str
    source: str
    published_at: datetime
    status: str = AnalysisStatus.INITIALIZED.value
    scraped_at: datetime = datetime.now(UTC)


class Article(ArticleCreate):
    """Pydantic model for article representation."""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Import related models after defining Article to avoid circular imports
from local_newsifier.models.database.entity import Entity
from local_newsifier.models.database.analysis_result import AnalysisResult

# Update forward references
Article.model_rebuild()