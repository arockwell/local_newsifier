"""Service layer for analysis operations."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable

from sqlmodel import Session
from fastapi_injectable import injectable
from typing import Annotated
from fastapi import Depends

from local_newsifier.crud.analysis_result import analysis_result
from local_newsifier.crud.article import article
from local_newsifier.crud.entity import entity
from local_newsifier.database.engine import SessionManager, get_session
from local_newsifier.errors import handle_database
from local_newsifier.models.analysis_result import AnalysisResult
from local_newsifier.models.trend import TrendAnalysis, TimeFrame


@injectable(use_cache=False)
class AnalysisService:
    """Service for analysis operations."""

    def __init__(
        self,
        analysis_result_crud,
        article_crud,
        entity_crud,
        trend_analyzer,
        session_factory: Callable,
    ):
        """Initialize the analysis service.

        Args:
            analysis_result_crud: CRUD component for analysis results
            article_crud: CRUD component for articles
            entity_crud: CRUD component for entities
            trend_analyzer: Tool for trend analysis
            session_factory: Factory function for creating database sessions
        """
        self.analysis_result_crud = analysis_result_crud
        self.article_crud = article_crud
        self.entity_crud = entity_crud
        self.trend_analyzer = trend_analyzer
        self.session_factory = session_factory

    @handle_database
    def analyze_headline_trends(
        self,
        start_date: datetime,