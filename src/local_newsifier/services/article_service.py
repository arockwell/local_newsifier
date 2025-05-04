"""Article service for coordinating article-related operations."""

from datetime import datetime
from typing import Callable, Dict, List, Optional, Any, TYPE_CHECKING

from local_newsifier.models.article import Article
from local_newsifier.models.analysis_result import AnalysisResult
from local_newsifier.database.engine import SessionManager
from local_newsifier.errors import handle_database

if TYPE_CHECKING:
    from local_newsifier.services.entity_service import EntityService


class ArticleService:
    """Service for article-related operations using the refactored architecture."""
    
    def __init__(
        self,
        article_crud,
        analysis_result_crud,
        entity_service_factory: Optional[Callable[[], 'EntityService']] = None,
        session_factory=None,
        # For backwards compatibility; will be removed
        entity_service=None,
        container=None
    ):
        """Initialize with dependencies.
        
        Args:
            article_crud: CRUD for articles
            analysis_result_crud: CRUD for analysis results
            entity_service_factory: Factory function to get EntityService instances
            session_factory: Factory for database sessions
            entity_service: Direct EntityService instance (legacy, will be deprecated)
            container: DI container for resolving dependencies (legacy, will be deprecated)
        """
        self.article_crud = article_crud
        self.analysis_result_crud = analysis_result_crud
        self._entity_service_factory = entity_service_factory
        self.session_factory = session_factory
        
        # Legacy support - will be removed in future
        self.entity_service = entity_service
        self.container = container
    
    def _get_entity_service(self):
        """Get the entity service, using the factory or falling back to legacy methods."""
        # First try the factory-based approach (new)
        if self._entity_service_factory is not None:
            return self._entity_service_factory()
            
        # Then try direct instance (legacy)
        if self.entity_service is not None:
            return self.entity_service
            
        # Finally try container (legacy)
        if self.container is not None:
            return self.container.get("entity_service")
            
        return None
        
    @handle_database
    def process_article(
        self, 
        url: str,
        content: str,
        title: str,
        published_at: datetime
    ) -> Dict[str, Any]:
        """Process an article including entity extraction and tracking.
        
        Args:
            url: URL of the article
            content: Article content
            title: Article title
            published_at: Article publication date
            
        Returns:
            Dictionary with article data and processing results
            
        Raises:
            ServiceError: On database errors with appropriate classification
        """
        with SessionManager() as session:
            # Extract domain as source if not provided
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            source = parsed_url.netloc or "Unknown Source"
            
            # Create article record
            article_data = Article(
                url=url,
                title=title,
                content=content,
                published_at=published_at,
                status="analyzed",
                source=source,
                scraped_at=datetime.now()
            )
            article = self.article_crud.create(session, obj_in=article_data)
            
            # Process entities using the entity service
            entity_service = self._get_entity_service()
            if not entity_service:
                raise ValueError("Entity service not available - cannot process article entities")
                
            entities = entity_service.process_article_entities(
                article_id=article.id,
                content=content,
                title=title,
                published_at=published_at
            )
            
            # Create analysis result
            entity_types = set(entity.get("canonical_type", "UNKNOWN") for entity in entities)
            entity_counts = {
                entity_type: len([e for e in entities if e.get("canonical_type", "UNKNOWN") == entity_type])
                for entity_type in entity_types
            }
            
            analysis_result_data = {
                "entities": entities,
                "statistics": {
                    "entity_counts": entity_counts,
                    "total_entities": len(entities)
                }
            }
            
            analysis_result_obj = AnalysisResult(
                article_id=article.id,
                analysis_type="entity_analysis",
                results=analysis_result_data  # Use the correct field name
            )
            
            analysis_result = self.analysis_result_crud.create(
                session, 
                obj_in=analysis_result_obj
            )
            
            # Commit the transaction
            session.commit()
            
            return {
                "article_id": article.id,
                "title": article.title,
                "url": article.url,
                "entities": entities,
                "analysis_result": analysis_result_data
            }
    
    @handle_database
    def get_article(self, article_id: int) -> Optional[Dict[str, Any]]:
        """Get article data by ID.
        
        Args:
            article_id: ID of the article
            
        Returns:
            Article data or None if not found
            
        Raises:
            ServiceError: On database errors with appropriate classification
        """
        with SessionManager() as session:
            article = self.article_crud.get(session, id=article_id)
            
            if not article:
                return None
                
            # Get analysis results
            analysis_results = self.analysis_result_crud.get_by_article(
                session, 
                article_id=article_id
            )
            
            return {
                "article_id": article.id,
                "title": article.title,
                "url": article.url,
                "content": article.content,
                "published_at": article.published_at,
                "status": article.status,
                "analysis_results": [result.results for result in analysis_results]
            }
    
    @handle_database
    def create_article_from_rss_entry(self, entry: Dict[str, Any]) -> Optional[int]:
        """Create a new article from an RSS feed entry.
        
        Args:
            entry: RSS feed entry data
            
        Returns:
            Created article or None if creation failed
            
        Raises:
            ServiceError: On database errors with appropriate classification
        """
        from datetime import datetime
        
        # Extract data from the RSS entry
        title = entry.get("title", "Untitled")
        url = entry.get("link", "")
        
        # Extract source from feed data or URL
        source = entry.get("source", {}).get("title", "")
        if not source and "feed_url" in entry:
            # Try to get domain from feed URL
            from urllib.parse import urlparse
            parsed_url = urlparse(entry.get("feed_url", ""))
            source = parsed_url.netloc
        
        # Fallback to domain name from article URL if source is still empty
        if not source and url:
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            source = parsed_url.netloc
            
        # Default source if all else fails
        if not source:
            source = "Unknown Source"
        
        # Handle published date parsing
        published_at = datetime.now()
        if "published" in entry:
            try:
                # Attempt to parse the published date
                from dateutil.parser import parse
                published_at = parse(entry["published"])
            except Exception:
                # Fall back to current date if parsing fails
                pass
        
        # Extract content
        content = ""
        if "content" in entry and len(entry["content"]) > 0:
            content = entry["content"][0].get("value", "")
        elif "summary" in entry:
            content = entry.get("summary", "")
        
        with self.session_factory() as session:
            # Create article object with source
            article_data = Article(
                title=title,
                url=url,
                content=content,
                published_at=published_at,
                status="new",
                source=source,
                scraped_at=datetime.now()
            )
            
            # Save to database
            article = self.article_crud.create(session, obj_in=article_data)
            
            return article.id if article else None
