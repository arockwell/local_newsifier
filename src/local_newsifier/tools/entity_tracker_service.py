"""Entity tracker tool that relies on :class:`EntityService`."""

from datetime import datetime
from typing import Annotated, Dict, List, Any

from fastapi import Depends
from fastapi_injectable import injectable
from sqlmodel import Session

from local_newsifier.database.engine import with_session
from local_newsifier.di.providers import get_entity_service, get_session
from local_newsifier.services.entity_service import EntityService


@injectable(use_cache=False)
class EntityTracker:
    """Tool for tracking entities across news articles."""

    def __init__(
        self,
        entity_service: Annotated[EntityService, Depends(get_entity_service)],
        session: Annotated[Session, Depends(get_session)],
    ) -> None:
        """Initialize the tracker with injected dependencies."""
        self.entity_service = entity_service
        self.session = session
        self.session_factory = lambda: session
    
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
        """Process an article to track entity mentions."""
        # Delegate to the service
        return self.entity_service.process_article_entities(
            article_id=article_id,
            content=content,
            title=title,
            published_at=published_at
        )