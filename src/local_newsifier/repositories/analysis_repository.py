"""Repository for handling analysis results in the database."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from ..models.database import AnalysisResultDB, ArticleDB
from ..models.state import AnalysisStatus, NewsAnalysisState


class AnalysisRepository:
    """Repository for managing analysis results in the database."""

    def __init__(self, session: Session):
        """
        Initialize the repository.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session

    def save(self, state: NewsAnalysisState) -> NewsAnalysisState:
        """
        Save analysis results to the database.

        Args:
            state: Current pipeline state

        Returns:
            Updated state
        """
        try:
            state.status = AnalysisStatus.SAVING
            state.add_log("Starting to save results to database")

            # Find or create article
            article = self.session.query(ArticleDB).filter_by(url=state.target_url).first()
            if not article:
                article = ArticleDB(
                    url=state.target_url,
                    title=state.scraped_title,
                    source=state.source,
                    published_at=state.published_at,
                    scraped_at=state.scraped_at,
                    content=state.scraped_text,
                    status="analyzed"
                )
                self.session.add(article)
                self.session.flush()  # Get the article ID

            # Create analysis result
            analysis_result = AnalysisResultDB(
                article_id=article.id,
                analysis_type="news_analysis",
                results={
                    "run_id": str(state.run_id),
                    "scraping": {
                        "timestamp": state.scraped_at.isoformat() if state.scraped_at else None,
                        "success": state.status in [AnalysisStatus.SCRAPE_SUCCEEDED, AnalysisStatus.COMPLETED_SUCCESS],
                        "text_length": len(state.scraped_text) if state.scraped_text else 0,
                    },
                    "analysis": {
                        "timestamp": state.analyzed_at.isoformat() if state.analyzed_at else None,
                        "success": state.status in [AnalysisStatus.ANALYSIS_SUCCEEDED, AnalysisStatus.COMPLETED_SUCCESS],
                        "config": state.analysis_config,
                        "results": state.analysis_results,
                    },
                    "metadata": {
                        "created_at": state.created_at.isoformat(),
                        "completed_at": state.last_updated.isoformat(),
                        "status": state.status,
                        "error": {
                            "task": state.error_details.task,
                            "type": state.error_details.type,
                            "message": state.error_details.message,
                        } if state.error_details else None,
                    },
                },
                created_at=datetime.now(timezone.utc)
            )
            self.session.add(analysis_result)
            self.session.commit()

            state.save_path = f"db://analysis_results/{analysis_result.id}"
            state.saved_at = datetime.now(timezone.utc)
            state.status = AnalysisStatus.SAVE_SUCCEEDED
            state.add_log(f"Successfully saved results to database with ID {analysis_result.id}")

            # If everything succeeded, mark as complete
            if state.status == AnalysisStatus.SAVE_SUCCEEDED and not state.error_details:
                state.status = AnalysisStatus.COMPLETED_SUCCESS
            else:
                state.status = AnalysisStatus.COMPLETED_WITH_ERRORS

        except Exception as e:
            self.session.rollback()
            state.status = AnalysisStatus.SAVE_FAILED
            state.set_error("saving", e)
            state.add_log(f"Error saving results to database: {str(e)}")
            raise

        return state

    def get(self, run_id: str) -> Optional[NewsAnalysisState]:
        """
        Get analysis results by run ID.

        Args:
            run_id: Run ID to look up

        Returns:
            NewsAnalysisState if found, None otherwise
        """
        result = self.session.query(AnalysisResultDB).join(ArticleDB).filter(
            AnalysisResultDB.results["run_id"].astext == run_id
        ).first()

        if not result:
            return None

        # Convert database result back to state
        # This would need to be implemented based on your state model
        raise NotImplementedError("State reconstruction not implemented")

    def list(self, filters: dict) -> list:
        """
        List analysis results with optional filters.

        Args:
            filters: Dictionary of filters to apply

        Returns:
            List of analysis results
        """
        query = self.session.query(AnalysisResultDB).join(ArticleDB)

        # Apply filters
        if "status" in filters:
            query = query.filter(AnalysisResultDB.results["metadata"]["status"].astext == filters["status"])
        if "date_from" in filters:
            query = query.filter(AnalysisResultDB.created_at >= filters["date_from"])
        if "date_to" in filters:
            query = query.filter(AnalysisResultDB.created_at <= filters["date_to"])

        return query.all() 