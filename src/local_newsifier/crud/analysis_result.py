"""CRUD operations for analysis results.

DEPRECATED: This thin wrapper is being removed. Use CRUDBase directly
or move queries to AnalysisService.
"""

import warnings
from typing import List, Optional

from sqlmodel import Session, select

from local_newsifier.crud.base import CRUDBase
from local_newsifier.models.analysis_result import AnalysisResult

warnings.warn(
    "CRUDAnalysisResult is deprecated. Use CRUDBase(AnalysisResult) directly "
    "or move queries to AnalysisService.",
    DeprecationWarning,
    stacklevel=2,
)


class CRUDAnalysisResult(CRUDBase[AnalysisResult]):
    """CRUD operations for analysis results."""

    def get_by_article(self, db: Session, *, article_id: int) -> List[AnalysisResult]:
        """Get all analysis results for an article.

        Args:
            db: Database session
            article_id: ID of the article

        Returns:
            List of analysis results for the article
        """
        results = db.execute(
            select(AnalysisResult).where(AnalysisResult.article_id == article_id)
        ).all()
        return [row[0] for row in results]

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
        result = db.execute(
            select(AnalysisResult).where(
                AnalysisResult.article_id == article_id,
                AnalysisResult.analysis_type == analysis_type,
            )
        ).first()
        return result[0] if result else None


analysis_result = CRUDAnalysisResult(AnalysisResult)
