"""Flow for processing news articles through the analysis pipeline."""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from sqlmodel import Session

from local_newsifier.flows.flow_base import FlowBase
from local_newsifier.di.descriptors import Dependency
from local_newsifier.models.state import AnalysisStatus, NewsAnalysisState
from local_newsifier.database.engine import SessionManager


class NewsPipelineFlow(FlowBase):
    """Flow for processing news articles through the analysis pipeline.
    
    This implementation uses the simplified DI pattern with descriptors
    for cleaner dependency declaration and resolution.
    """
    
    # Define dependencies using descriptors - these will be lazy-loaded when needed
    scraper = Dependency()
    file_writer = Dependency()
    pipeline_service = Dependency()
    article_service = Dependency()
    entity_service = Dependency()
    entity_extractor = Dependency()
    context_analyzer = Dependency()
    entity_resolver = Dependency()
    session_factory = Dependency(fallback=SessionManager)
    
    def __init__(
        self,
        container=None,
        session: Optional[Session] = None,
        **explicit_deps
    ):
        """Initialize the news pipeline flow.
        
        Args:
            container: Optional DI container for resolving dependencies
            session: Optional database session (for direct use)
            **explicit_deps: Explicit dependencies (overrides container)
        """
        # Initialize the FlowBase
        super().__init__(container, **explicit_deps)
            
        self.session = session

    def ensure_dependencies(self) -> None:
        """Ensure all required dependencies are available."""
        # Access dependencies to trigger lazy loading
        assert self.pipeline_service is not None, "NewsPipelineService is required"
        assert self.article_service is not None, "ArticleService is required"
        # Other dependencies will be loaded when needed
    
    def process(self, state: NewsAnalysisState) -> NewsAnalysisState:
        """Process an article for analysis through the pipeline.
        
        Args:
            state: NewsAnalysisState containing article info
            
        Returns:
            Updated state with analysis results
        """
        try:
            return self.pipeline_service.process_article_with_state(state)
        except Exception as e:
            # Handle errors by updating the state
            state.status = AnalysisStatus.FAILED
            state.set_error("pipeline_processing", e)
            state.add_log(f"Error processing article: {str(e)}")
            return state

    def process_article(self, article_id: int) -> Dict[str, Any]:
        """Legacy method for processing a single article by ID.
        
        Args:
            article_id: ID of the article to process
            
        Returns:
            Dictionary with analysis results
        """
        from local_newsifier.crud.article import article as article_crud
        
        with self.session_factory() as session:
            # Get article
            article = article_crud.get(session, id=article_id)
                
            if not article:
                raise ValueError(f"Article with ID {article_id} not found")
            
            # Create state for processing
            state = NewsAnalysisState(
                article_id=article.id,
                content=article.content,
                title=article.title,
                url=article.url or "",
                published_at=article.published_at or datetime.now(timezone.utc)
            )
            
            # Process article
            result_state = self.process(state)
            
            # Return processed results
            return {
                "status": result_state.status.value,
                "entities": result_state.entities,
                "sentiment": result_state.sentiment_score,
                "topics": result_state.topics,
                "summary": result_state.summary
            }

    def analyze_with_url(self, url: str) -> Dict[str, Any]:
        """Process a new article from a URL.
        
        Args:
            url: URL of the article to process
            
        Returns:
            Dictionary with analysis results
        """
        if not self.scraper:
            raise ValueError("Web scraper is required for URL processing")
        
        # Scrape the article
        scraped_data = self.scraper.scrape_article(url)
        
        if not scraped_data or not scraped_data.get("content"):
            raise ValueError(f"Failed to scrape content from URL: {url}")
        
        # Create state for processing
        state = NewsAnalysisState(
            content=scraped_data.get("content", ""),
            title=scraped_data.get("title", ""),
            url=url,
            published_at=scraped_data.get("published_at") or datetime.now(timezone.utc)
        )
        
        # Process article
        result_state = self.process(state)
        
        # Store article if requested
        if result_state.save_article and result_state.status == AnalysisStatus.SUCCESS:
            with self.session_factory() as session:
                self.article_service.create_article_from_state(session, result_state)
        
        # Return processed results
        return {
            "status": result_state.status.value,
            "entities": result_state.entities,
            "sentiment": result_state.sentiment_score,
            "topics": result_state.topics,
            "summary": result_state.summary
        }

    def analyze_with_text(self, content: str, title: str = "", url: str = "") -> Dict[str, Any]:
        """Process a new article from raw text content.
        
        Args:
            content: Text content of the article
            title: Optional title of the article
            url: Optional source URL of the article
            
        Returns:
            Dictionary with analysis results
        """
        # Create state for processing
        state = NewsAnalysisState(
            content=content,
            title=title,
            url=url,
            published_at=datetime.now(timezone.utc)
        )
        
        # Process article
        result_state = self.process(state)
        
        # Store article if requested
        if result_state.save_article and result_state.status == AnalysisStatus.SUCCESS:
            with self.session_factory() as session:
                self.article_service.create_article_from_state(session, result_state)
        
        # Return processed results
        return {
            "status": result_state.status.value,
            "entities": result_state.entities,
            "sentiment": result_state.sentiment_score,
            "topics": result_state.topics,
            "summary": result_state.summary
        }
