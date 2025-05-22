"""Entity tracker tool that uses the EntityService."""

from datetime import datetime
from typing import Dict, List, Any

from sqlmodel import Session

from local_newsifier.database.engine import with_session
from local_newsifier.services.entity_service import EntityService


class EntityTracker:
    """Tool for tracking entities across news articles using the EntityService."""

    def __init__(self, entity_service: EntityService) -> None:
        """Initialize the tracker with an entity service.

        Args:
            entity_service: Service for entity operations
        """
        self.entity_service = entity_service
    
    @with_session
    def process_article(
        self, 
        article_id: int,
        content: str,
        title: str,
        published_at: datetime,
        *,
        session: Session = None
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