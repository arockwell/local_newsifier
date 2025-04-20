"""Article service for coordinating article-related operations."""

from datetime import datetime
from typing import Dict, List, Optional, Any

from local_newsifier.models.article import Article
from local_newsifier.models.analysis_result import AnalysisResult
from local_newsifier.services.entity_service import EntityService
from local_newsifier.database.engine import SessionManager


class ArticleService:
    """Service for article-related operations using the refactored architecture."""
    
    def __init__(
        self,
        article_crud,
        analysis_result_crud,
        entity_service,
        session_factory=None
    ):
        """Initialize with dependencies.
        
        Args:
            article_crud: CRUD for articles
            analysis_result_crud: CRUD for analysis results
            entity_service: Service for entity operations
            session_factory: Factory for database sessions
        """
        self.article_crud = article_crud
        self.analysis_result_crud = analysis_result_crud
        self.entity_service = entity_service
        self.session_factory = session_factory
    
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
        """
        with SessionManager() as session:
            # Create article record
            article_data = Article(
                url=url,
                title=title,
                content=content,
                published_at=published_at,
                status="analyzed"
            )
            article = self.article_crud.create(session, obj_in=article_data)
            
            # Process entities using the entity service
            entities = self.entity_service.process_article_entities(
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
    
    def get_article(self, article_id: int) -> Optional[Dict[str, Any]]:
        """Get article data by ID.
        
        Args:
            article_id: ID of the article
            
        Returns:
            Article data or None if not found
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
