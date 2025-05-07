"""Entity tracker tool that uses the EntityService."""

from datetime import datetime
from typing import Annotated, Dict, List, Optional, Any

from fastapi import Depends
from fastapi_injectable import injectable
from sqlmodel import Session

from local_newsifier.services.entity_service import EntityService


@injectable(use_cache=False)
class EntityTracker:
    """Tool for tracking entities across news articles using the EntityService.
    
    Uses the injectable pattern for dependency injection. This class does not
    create its own dependencies but expects them to be injected.
    
    Attributes:
        entity_service: Service for entity operations
    """
    
    def __init__(
        self, 
        entity_service: Optional[EntityService] = None
    ):
        """Initialize with optional injected dependencies.
        
        Args:
            entity_service: Service for entity operations, 
                will be injected by the container when needed
        """
        self.entity_service = entity_service
    
    def process_article(
        self, 
        article_id: int,
        content: str,
        title: str,
        published_at: datetime
    ) -> List[Dict[str, Any]]:
        """Process an article to track entity mentions.
        
        Args:
            article_id: ID of the article being processed
            content: Article content
            title: Article title
            published_at: Article publication date
            session: Database session
            
        Returns:
            List of processed entity mentions
        """
        # Delegate to the service
        return self.entity_service.process_article_entities(
            article_id=article_id,
            content=content,
            title=title,
            published_at=published_at
        )
