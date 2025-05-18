"""Article service for coordinating article-related operations."""

from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Union

from fastapi_injectable import injectable
from typing import Annotated
from fastapi import Depends

from local_newsifier.models.article import Article
from local_newsifier.models.analysis_result import AnalysisResult
from local_newsifier.errors import handle_database


@injectable(use_cache=False)
class ArticleService:
    """Service for article-related operations using the refactored architecture."""
    
    def __init__(
        self,
        article_crud,
        analysis_result_crud,
        entity_service,
        session_factory: Callable,
        article_preprocessor=None,
    ):
        """Initialize with dependencies.
        
        Args:
            article_crud: CRUD for articles
            analysis_result_crud: CRUD for analysis results
            entity_service: Service for entity operations
            session_factory: Factory for database sessions
            article_preprocessor: Optional preprocessor for article content
        """
        self.article_crud = article_crud
        self.analysis_result_crud = analysis_result_crud
        self.entity_service = entity_service
        self.session_factory = session_factory
        self.article_preprocessor = article_preprocessor
        
    @handle_database
    def process_article(
        self, 
        url: str,
        content: str,
        title: str,
        published_at: datetime,
        html_content: Optional[str] = None,
        preprocess: bool = True
    ) -> Dict[str, Any]:
        """Process an article including preprocessing, entity extraction and tracking.
        
        Args:
            url: URL of the article
            content: Article content
            title: Article title
            published_at: Article publication date
            html_content: Optional HTML content for better preprocessing
            preprocess: Whether to preprocess the article content
            
        Returns:
            Dictionary with article data and processing results
            
        Raises:
            ServiceError: On database errors with appropriate classification
        """
        with self.session_factory() as session:
            # Extract domain as source if not provided
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            source = parsed_url.netloc or "Unknown Source"
            
            # Prepare article data
            article_data = {
                "url": url,
                "title": title,
                "content": content,
                "published_at": published_at,
                "status": "new",
                "source": source,
                "scraped_at": datetime.now()
            }
            
            # Apply preprocessing if enabled and preprocessor is available
            preprocessed_data = None
            if preprocess and self.article_preprocessor:
                preprocessed_data = self.article_preprocessor.preprocess_article_data(
                    article_data=article_data.copy(),
                    html_content=html_content
                )
                
                # Update article data with preprocessed content and metadata
                article_data["content"] = preprocessed_data["content"]
                article_data["title"] = preprocessed_data.get("title", title)
                article_data["source"] = preprocessed_data.get("source", source)
                
                if "published_at" in preprocessed_data and preprocessed_data["published_at"]:
                    article_data["published_at"] = preprocessed_data["published_at"]
                
                # Store additional metadata in structures field if available
                if "structures" in preprocessed_data:
                    article_data["metadata"] = {"structures": preprocessed_data["structures"]}
                
                # Update article status to preprocessed
                article_data["status"] = "preprocessed"
            
            # Create article record
            article_obj = Article(**article_data)
            article = self.article_crud.create(session, obj_in=article_obj)
            
            # Process entities using the entity service
            entities = self.entity_service.process_article_entities(
                article_id=article.id,
                content=article_data["content"],
                title=article_data["title"],
                published_at=article_data["published_at"]
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
            
            # Include preprocessing metadata if available
            if preprocessed_data and "metadata" in preprocessed_data:
                metadata_to_store = {}
                
                # Add relevant preprocessing metadata
                for key in ["categories", "language", "locations", "word_count"]:
                    if key in preprocessed_data["metadata"]:
                        metadata_to_store[key] = preprocessed_data["metadata"][key]
                
                if metadata_to_store:
                    analysis_result_data["preprocessing_metadata"] = metadata_to_store
            
            analysis_result_obj = AnalysisResult(
                article_id=article.id,
                analysis_type="entity_analysis",
                results=analysis_result_data
            )
            
            analysis_result = self.analysis_result_crud.create(
                session, 
                obj_in=analysis_result_obj
            )
            
            # Update article status to analyzed
            article.status = "analyzed"
            session.add(article)
            session.commit()
            
            result = {
                "article_id": article.id,
                "title": article.title,
                "url": article.url,
                "entities": entities,
                "analysis_result": analysis_result_data
            }
            
            # Include preprocessing result if available
            if preprocessed_data:
                result["preprocessing"] = {
                    "cleaned_content": preprocessed_data.get("content", content),
                    "metadata": preprocessed_data.get("metadata", {})
                }
            
            return result
    
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
        with self.session_factory() as session:
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
    def create_article_from_rss_entry(
        self, 
        entry: Dict[str, Any],
        preprocess: bool = True,
        html_content: Optional[str] = None
    ) -> Optional[int]:
        """Create a new article from an RSS feed entry.
        
        Args:
            entry: RSS feed entry data
            preprocess: Whether to preprocess the article content
            html_content: Optional HTML content for better preprocessing
            
        Returns:
            Created article ID or None if creation failed
            
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
            
        # Use entry HTML content if provided in the entry
        entry_html = None
        if not html_content:
            # Try to get HTML content from the entry
            if "content" in entry and len(entry["content"]) > 0:
                entry_html = entry["content"][0].get("value", "")
        else:
            entry_html = html_content
        
        # Prepare article data dictionary
        article_data = {
            "title": title,
            "url": url,
            "content": content,
            "published_at": published_at,
            "status": "new",
            "source": source,
            "scraped_at": datetime.now()
        }
        
        # Apply preprocessing if enabled and preprocessor is available
        if preprocess and self.article_preprocessor and (content or entry_html):
            preprocessed_data = self.article_preprocessor.preprocess_article_data(
                article_data=article_data.copy(),
                html_content=entry_html
            )
            
            # Update article data with preprocessed content and metadata
            article_data["content"] = preprocessed_data["content"]
            
            # Preserve the original title if the preprocessor didn't find a better one
            if "title" in preprocessed_data and preprocessed_data["title"] and len(preprocessed_data["title"]) > len(title):
                article_data["title"] = preprocessed_data["title"]
                
            if "source" in preprocessed_data and preprocessed_data["source"]:
                article_data["source"] = preprocessed_data["source"]
                
            if "published_at" in preprocessed_data and preprocessed_data["published_at"]:
                article_data["published_at"] = preprocessed_data["published_at"]
                
            # Store additional metadata in structures field if available
            if "structures" in preprocessed_data:
                article_data["metadata"] = {"structures": preprocessed_data["structures"]}
                
            # Update article status to preprocessed
            article_data["status"] = "preprocessed"
        
        with self.session_factory() as session:
            # Create article object
            article_obj = Article(**article_data)
            
            # Save to database
            article = self.article_crud.create(session, obj_in=article_obj)
            
            # Commit changes to ensure they're persisted
            session.commit()
            
            return article.id if article else None
