"""Dependency injection providers using CRUDBase directly.

This shows how to eliminate thin CRUD wrappers by using CRUDBase directly.
"""

from local_newsifier.crud.base import CRUDBase
from local_newsifier.models.analysis_result import AnalysisResult
from local_newsifier.models.entity import Entity
from local_newsifier.models.rss_feed import RSSFeed


def get_analysis_result_crud():
    """Get CRUD for analysis results using CRUDBase directly."""
    return CRUDBase(AnalysisResult)


def get_entity_crud():
    """Get CRUD for entities using CRUDBase directly."""
    return CRUDBase(Entity)


def get_rss_feed_crud():
    """Get CRUD for RSS feeds using CRUDBase directly."""
    return CRUDBase(RSSFeed)


# Example of how services can implement the custom queries
class SimplifiedAnalysisService:
    """Example showing queries moved from CRUD to service."""

    def __init__(self, session_factory):
        """Initialize with session factory."""
        self.session_factory = session_factory
        self.crud = CRUDBase(AnalysisResult)

    def get_by_article(self, article_id: int):
        """Get analysis results for an article."""
        from sqlmodel import select

        with self.session_factory() as session:
            results = session.exec(
                select(AnalysisResult).where(AnalysisResult.article_id == article_id)
            ).all()
            return results

    def get_by_article_and_type(self, article_id: int, analysis_type: str):
        """Get specific analysis type for an article."""
        from sqlmodel import select

        with self.session_factory() as session:
            result = session.exec(
                select(AnalysisResult).where(
                    AnalysisResult.article_id == article_id,
                    AnalysisResult.analysis_type == analysis_type,
                )
            ).first()
            return result
