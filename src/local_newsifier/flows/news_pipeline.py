from datetime import datetime, timezone
from typing import Annotated, Optional

from crewai import Flow
from fastapi import Depends
from fastapi_injectable import injectable
from sqlmodel import Session

from local_newsifier.models.state import AnalysisStatus, NewsAnalysisState
from local_newsifier.tools.file_writer import FileWriterTool
from local_newsifier.tools.web_scraper import WebScraperTool
from local_newsifier.services.news_pipeline_service import NewsPipelineService
from local_newsifier.services.article_service import ArticleService
from local_newsifier.services.entity_service import EntityService


@injectable(use_cache=False)
class NewsPipelineFlow(Flow):
    """Flow for processing news articles with NER analysis."""

    def __init__(
        self, 
        article_service: ArticleService,
        entity_service: EntityService,
        pipeline_service: NewsPipelineService,
        web_scraper: WebScraperTool,
        file_writer: FileWriterTool,
        session: Session
    ):
        """Initialize the pipeline flow with injected dependencies.
        
        Args:
            article_service: Service for article operations
            entity_service: Service for entity operations
            pipeline_service: Service for news pipeline operations
            web_scraper: Tool for scraping web content
            file_writer: Tool for writing files
            session: Database session
        """
        super().__init__()
        
        self.scraper = web_scraper
        self.writer = file_writer
        self.session = session
        self.entity_service = entity_service
        self.article_service = article_service
        self.pipeline_service = pipeline_service

    def scrape_content(self, state: NewsAnalysisState) -> NewsAnalysisState:
        """Task for scraping article content."""
        return self.scraper.scrape(state)

    def process_content(self, state: NewsAnalysisState) -> NewsAnalysisState:
        """Task for processing article content including entity tracking."""
        try:
            state.status = AnalysisStatus.ANALYZING
            state.add_log("Starting article processing with entity tracking")

            if not state.scraped_text:
                raise ValueError("No text content available for processing")

            # Process article using the service
            result = self.article_service.process_article(
                url=state.target_url,
                content=state.scraped_text,
                title=state.scraped_title if hasattr(state, 'scraped_title') else "Untitled Article",
                published_at=state.scraped_at or datetime.now(timezone.utc)
            )

            # Update state with results
            state.analysis_results = result["analysis_result"]
            state.analyzed_at = datetime.now(timezone.utc)
            state.status = AnalysisStatus.ANALYSIS_SUCCEEDED
            state.add_log(
                f"Successfully completed article processing. "
                f"Found {result['analysis_result']['statistics']['total_entities']} entities."
            )

        except Exception as e:
            state.status = AnalysisStatus.ANALYSIS_FAILED
            state.set_error("analysis", e)
            state.add_log(f"Error during article processing: {str(e)}")
            # Don't re-raise the exception, just return the state with error

        return state

    def save_results(self, state: NewsAnalysisState) -> NewsAnalysisState:
        """Task for saving analysis results."""
        return self.writer.save(state)

    def start_pipeline(self, url: str) -> NewsAnalysisState:
        """
        Start the pipeline with a URL.

        Args:
            url: URL of the article to analyze

        Returns:
            Final pipeline state
        """
        # Initialize state
        state = NewsAnalysisState(target_url=url)
        state.add_log(f"Starting pipeline for URL: {url}")

        # Execute pipeline
        state = self.scrape_content(state)
        if state.status not in [AnalysisStatus.SCRAPE_SUCCEEDED]:
            return state

        state = self.process_content(state)
        if state.status not in [AnalysisStatus.ANALYSIS_SUCCEEDED]:
            return state

        state = self.save_results(state)
        return state

    def resume_pipeline(
        self, run_id: str, state: Optional[NewsAnalysisState] = None
    ) -> NewsAnalysisState:
        """
        Resume a pipeline from its last successful state.

        Args:
            run_id: ID of the run to resume
            state: Optional state to resume from

        Returns:
            Final pipeline state
        """
        if not state:
            # In a real implementation, we would load state from SQLite
            raise NotImplementedError("State loading not implemented")

        state.add_log(f"Resuming pipeline for run_id: {run_id}")

        # Determine where to resume based on status
        if state.status in [
            AnalysisStatus.INITIALIZED,
            AnalysisStatus.SCRAPE_FAILED_NETWORK,
            AnalysisStatus.SCRAPE_FAILED_PARSING,
        ]:
            # Clear any previous error details before retrying
            if state.status in [
                AnalysisStatus.SCRAPE_FAILED_NETWORK,
                AnalysisStatus.SCRAPE_FAILED_PARSING,
            ]:
                state.error_details = None
                state.add_log("Retry attempt for scraping")

            state = self.scrape_content(state)
            if state.status not in [AnalysisStatus.SCRAPE_SUCCEEDED]:
                return state

            state = self.process_content(state)
            if state.status not in [AnalysisStatus.ANALYSIS_SUCCEEDED]:
                return state

            state = self.save_results(state)

        elif state.status in [
            AnalysisStatus.SCRAPE_SUCCEEDED,
            AnalysisStatus.ANALYSIS_FAILED,
        ]:
            # Clear any previous error details before retrying
            if state.status == AnalysisStatus.ANALYSIS_FAILED:
                state.error_details = None
                state.add_log("Retry attempt for analysis")

            state = self.process_content(state)
            if state.status not in [AnalysisStatus.ANALYSIS_SUCCEEDED]:
                return state

            state = self.save_results(state)

        elif state.status in [
            AnalysisStatus.ANALYSIS_SUCCEEDED,
            AnalysisStatus.SAVE_FAILED,
        ]:
            # Clear any previous error details before retrying
            if state.status == AnalysisStatus.SAVE_FAILED:
                state.error_details = None
                state.add_log("Retry attempt for saving")

            state = self.save_results(state)

        else:
            state.add_log(f"Cannot resume from status: {state.status}")
            raise ValueError(f"Cannot resume from status: {state.status}")

        return state
    
    def process_url_directly(self, url: str) -> dict:
        """
        Process a URL directly using the pipeline service.
        
        Args:
            url: URL of the article to process
            
        Returns:
            Dictionary with processing results
        """
        return self.pipeline_service.process_url(url)
