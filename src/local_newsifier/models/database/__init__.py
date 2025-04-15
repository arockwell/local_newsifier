"""
LEGACY DATABASE MODELS PACKAGE - DO NOT USE

This package is deprecated and exists only for backward compatibility.
Please use the SQLModel-based models instead:

from local_newsifier.models import Article, Entity, AnalysisResult
"""

# Re-export stubs for backward compatibility
from local_newsifier.models.database.base import Base
from local_newsifier.models.database.article import ArticleDB
from local_newsifier.models.database.entity import EntityDB
from local_newsifier.models.database.analysis_result import AnalysisResultDB

# Re-export all models
__all__ = [
    "Base",
    "ArticleDB",
    "EntityDB",
    "AnalysisResultDB"
]