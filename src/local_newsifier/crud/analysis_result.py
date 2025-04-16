"""CRUD operations for analysis results."""

from typing import List, Optional

from sqlmodel import Session, select

from local_newsifier.crud.base import CRUDBase
from local_newsifier.models.database.analysis_result import AnalysisResult


class CRUDAnalysisResult(CRUDBase[AnalysisResult]):
    """CRUD operations for analysis results."""

    def get_by_article(
        self, db: Session, *, article_id: int
    ) -> List[AnalysisResult]:
        """Get all analysis results for an article.

        Args:
            db: Database session
            article_id: ID of the article

        Returns:
            List of analysis results for the article
        """
        statement = select(AnalysisResult).where(AnalysisResult.article_id == article_id)
        results = db.exec(statement)
        return results.all()

    def get_by_article_and_type(
        self, db: Session, *, article_id: int, analysis_type: str
    ) -> Optional[AnalysisResult]:
        """Get an analysis result by article ID and type.

        Args:
            db: Database session
            article_id: ID of the article
            analysis_type: Type of analysis

        Returns:
            Analysis result if found, None otherwise
        """
        statement = select(AnalysisResult).where(
            AnalysisResult.article_id == article_id,
            AnalysisResult.analysis_type == analysis_type
        )
        results = db.exec(statement)
        return results.first()


analysis_result = CRUDAnalysisResult(AnalysisResult)
