"""Entity tracker tool that delegates to :class:`EntityService`."""

from datetime import datetime
from typing import Dict, List, Any

from local_newsifier.services.entity_service import EntityService


class EntityTracker:
    """Thin wrapper around :class:`EntityService`."""

    def __init__(self, entity_service: EntityService) -> None:
        """Store the injected :class:`EntityService`."""
        self.entity_service = entity_service

    def process_article(
        self,
        article_id: int,
        content: str,
        title: str,
        published_at: datetime,
    ) -> List[Dict[str, Any]]:
        """Process an article and return tracked entities."""
        return self.entity_service.process_article_entities(
            article_id=article_id,
            content=content,
            title=title,
            published_at=published_at,
        )
