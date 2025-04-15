"""
LEGACY PYDANTIC MODELS - DO NOT USE

This module is deprecated and exists only for backward compatibility.
Please use the SQLModel-based models instead:

from local_newsifier.models import Article, Entity, AnalysisResult
"""

# Re-export SQLModel models for compatibility
from local_newsifier.models import Article, Entity, AnalysisResult

# For backward compatibility - these classes should not be used in new code
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class ArticleBase(BaseModel):
    """Base Pydantic model for articles. DEPRECATED - use SQLModel Article instead."""
    url: str
    title: Optional[str] = None
    source: Optional[str] = None
    published_at: Optional[datetime] = None
    content: Optional[str] = None
    status: Optional[str] = None


class ArticleCreate(ArticleBase):
    """Pydantic model for creating articles. DEPRECATED - use SQLModel Article instead."""
    pass


class EntityBase(BaseModel):
    """Base Pydantic model for entities. DEPRECATED - use SQLModel Entity instead."""
    text: str
    entity_type: str
    confidence: float


class EntityCreate(EntityBase):
    """Pydantic model for creating entities. DEPRECATED - use SQLModel Entity instead."""
    article_id: int


class AnalysisResultBase(BaseModel):
    """Base Pydantic model for analysis results. DEPRECATED - use SQLModel AnalysisResult instead."""
    analysis_type: str
    results: Dict[str, Any]


class AnalysisResultCreate(AnalysisResultBase):
    """Pydantic model for creating analysis results. DEPRECATED - use SQLModel AnalysisResult instead."""
    article_id: int