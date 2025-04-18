"""Analysis result models for the news analysis system."""

from typing import Dict, Any, Optional, TYPE_CHECKING

from sqlmodel import Field, Relationship, JSON

from local_newsifier.models.database.base import TableBase

# Handle circular imports
if TYPE_CHECKING:
    from local_newsifier.models.database.article import Article


class AnalysisResult(TableBase, table=True):
    """SQLModel for analysis results."""

    __tablename__ = "analysis_results"
    
    # Handle multiple imports during test collection
    __table_args__ = {"extend_existing": True}

    article_id: int = Field(foreign_key="articles.id")
    analysis_type: str
    results: Dict[str, Any] = Field(sa_type=JSON)
    
    # Define relationship with fully qualified path
    article: Optional["local_newsifier.models.database.article.Article"] = Relationship(back_populates="analysis_results")