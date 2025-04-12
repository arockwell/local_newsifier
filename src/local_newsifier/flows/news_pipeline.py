from typing import Optional

from crewai import Flow

from ..models.state import NewsAnalysisState, AnalysisStatus
from ..tools.file_writer import FileWriterTool
from ..tools.ner_analyzer import NERAnalyzerTool
from ..tools.web_scraper import WebScraperTool


class NewsPipelineFlow(Flow):
    """Flow for processing news articles with NER analysis."""

    def __init__(self, output_dir: str = "output"):
        """Initialize the pipeline flow."""
        super().__init__()
        self.scraper = WebScraperTool()
        self.analyzer = NERAnalyzerTool()
        self.writer = FileWriterTool(output_dir=output_dir)

    def scrape_content(self, state: NewsAnalysisState) -> NewsAnalysisState:
        """Task for scraping article content."""
        return self.scraper.scrape(state)

    def analyze_content(self, state: NewsAnalysisState) -> NewsAnalysisState:
        """Task for performing NER analysis."""
        return self.analyzer.analyze(state)

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
            
        state = self.analyze_content(state)
        if state.status not in [AnalysisStatus.ANALYSIS_SUCCEEDED]:
            return state
            
        state = self.save_results(state)
        return state

    def resume_pipeline(self, run_id: str, state: Optional[NewsAnalysisState] = None) -> NewsAnalysisState:
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
            AnalysisStatus.SCRAPE_FAILED_PARSING
        ]:
            # Clear any previous error details before retrying
            if state.status in [AnalysisStatus.SCRAPE_FAILED_NETWORK, AnalysisStatus.SCRAPE_FAILED_PARSING]:
                state.error_details = None
                state.add_log("Retry attempt for scraping")
            
            state = self.scrape_content(state)
            if state.status not in [AnalysisStatus.SCRAPE_SUCCEEDED]:
                return state
                
            state = self.analyze_content(state)
            if state.status not in [AnalysisStatus.ANALYSIS_SUCCEEDED]:
                return state
                
            state = self.save_results(state)
            
        elif state.status in [
            AnalysisStatus.SCRAPE_SUCCEEDED,
            AnalysisStatus.ANALYSIS_FAILED
        ]:
            # Clear any previous error details before retrying
            if state.status == AnalysisStatus.ANALYSIS_FAILED:
                state.error_details = None
                state.add_log("Retry attempt for analysis")
            
            state = self.analyze_content(state)
            if state.status not in [AnalysisStatus.ANALYSIS_SUCCEEDED]:
                return state
                
            state = self.save_results(state)
            
        elif state.status in [
            AnalysisStatus.ANALYSIS_SUCCEEDED,
            AnalysisStatus.SAVE_FAILED
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