from datetime import datetime, timezone
from typing import Optional

from crewai import Flow

from local_newsifier.models.state import AnalysisStatus, NewsAnalysisState
from local_newsifier.tools.file_writer import FileWriterTool
from local_newsifier.tools.web_scraper import WebScraperTool
from local_newsifier.services.news_pipeline_service import NewsPipelineService
from local_newsifier.services.article_service import ArticleService
from local_newsifier.services.entity_service import EntityService
from local_newsifier.database.engine import get_session
from local_newsifier.crud.article import article as article_crud
from local_newsifier.crud.analysis_result import analysis_result as analysis_result_crud
from local_newsifier.crud.entity import entity as entity_crud
from local_newsifier.crud.canonical_entity import canonical_entity as canonical_entity_crud
from local_newsifier.crud.entity_mention_context import entity_mention_context as entity_mention_context_crud
from local_newsifier.crud.entity_profile import entity_profile as entity_profile_crud
from local_newsifier.tools.extraction.entity_extractor import EntityExtractor
from local_newsifier.tools.analysis.context_analyzer import ContextAnalyzer
from local_newsifier.tools.resolution.entity_resolver import EntityResolver


class NewsPipelineFlow(Flow):
    """Flow for processing news articles with NER analysis."""

    def __init__(self, output_dir: str = "output"):
        """Initialize the pipeline flow."""
        super().__init__()
        # Create basic tools
        self.scraper = WebScraperTool()
        self.writer = FileWriterTool(output_dir=output_dir)
        
        # Create entity service
        self.entity_service = EntityService(
            entity_crud=entity_crud,
            canonical_entity_crud=canonical_entity_crud,
            entity_mention_context_crud=entity_mention_context_crud,
            entity_profile_crud=entity_profile_crud,
            article_crud=article_crud,  # Added missing article_crud parameter
            entity_extractor=EntityExtractor(),
            context_analyzer=ContextAnalyzer(),
            entity_resolver=EntityResolver(),
            session_factory=get_session
        )
        
        # Create article service
        self.article_service = ArticleService(
            article_crud=article_crud,
            analysis_result_crud=analysis_result_crud,
            entity_service=self.entity_service,
            session_factory=get_session
        )
        
        # Create pipeline service
        self.pipeline_service = NewsPipelineService(
            article_service=self.article_service,
            web_scraper=self.scraper,
            file_writer=self.writer,
            session_factory=get_session
        )

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
