"""Pydantic models for the database."""

from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel


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


class EntityBase(BaseModel):
    """Base Pydantic model for entities."""

    text: str
    entity_type: str
    confidence: float


class EntityCreate(EntityBase):
    """Pydantic model for creating entities."""

    article_id: int


class Entity(EntityBase):
    """Pydantic model for entities with relationships."""

    id: int
    article_id: int

    class Config:
        """Pydantic config."""

        from_attributes = True


class AnalysisResultBase(BaseModel):
    """Base Pydantic model for analysis results."""

    analysis_type: str
    results: Dict[str, Any]


class AnalysisResultCreate(AnalysisResultBase):
    """Pydantic model for creating analysis results."""

    article_id: int


class AnalysisResult(AnalysisResultBase):
    """Pydantic model for analysis results with relationships."""

    id: int
    article_id: int
    created_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


# Update forward references
Article.model_rebuild()
Entity.model_rebuild()
AnalysisResult.model_rebuild() 