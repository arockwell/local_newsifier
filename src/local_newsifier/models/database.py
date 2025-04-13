"""Database models for the news analysis system."""

import enum
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from pydantic import BaseModel
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

# Import directly from submodules to avoid circular imports
from local_newsifier.models.database.base import Base
from local_newsifier.models.database.article import ArticleDB
from local_newsifier.models.database.entity import EntityDB
from local_newsifier.models.database.analysis_result import AnalysisResultDB
from local_newsifier.models.database import init_db, get_session


# Pydantic Models
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
    results: dict


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


# Re-export initialization functions
__all__ = [
    "Base",
    "ArticleDB",
    "EntityDB", 
    "AnalysisResultDB",
    "ArticleBase",
    "ArticleCreate",
    "Article",
    "EntityBase",
    "EntityCreate",
    "Entity",
    "AnalysisResultBase",
    "AnalysisResultCreate",
    "AnalysisResult",
    "init_db",
    "get_session"
]