"""Analysis result models for the news analysis system."""

from typing import Dict, Any, Optional, TYPE_CHECKING

from sqlmodel import Field, Relationship

from local_newsifier.models.database.base import TableBase

# Handle circular imports
if TYPE_CHECKING:
    from local_newsifier.models.database.article import Article


class AnalysisResult(TableBase, table=True):
    """SQLModel for analysis results."""

    __tablename__ = "analysis_results"

    article_id: int = Field(foreign_key="articles.id")
    analysis_type: str
    results: Dict[str, Any]
    
    # Define relationship
    article: Optional["Article"] = Relationship(back_populates="analysis_results")