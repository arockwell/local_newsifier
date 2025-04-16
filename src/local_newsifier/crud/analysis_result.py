"""CRUD operations for analysis results."""

from typing import List, Optional

from sqlalchemy.orm import Session

from local_newsifier.crud.base import CRUDBase
from local_newsifier.models.database.analysis_result import AnalysisResultDB
from local_newsifier.models.pydantic_models import (AnalysisResult,
                                                    AnalysisResultCreate)


class CRUDAnalysisResult(
    CRUDBase[AnalysisResultDB, AnalysisResultCreate, AnalysisResult]
):
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
        db_results = (
            db.query(AnalysisResultDB)
            .filter(AnalysisResultDB.article_id == article_id)
            .all()
        )
        return [AnalysisResult.model_validate(result) for result in db_results]

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
        db_result = (
            db.query(AnalysisResultDB)
            .filter(
                AnalysisResultDB.article_id == article_id,
                AnalysisResultDB.analysis_type == analysis_type,
            )
            .first()
        )
        return AnalysisResult.model_validate(db_result) if db_result else None


analysis_result = CRUDAnalysisResult(AnalysisResultDB, AnalysisResult)
