"""Entity service for managing entity-related business logic."""

from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlmodel import Session

from local_newsifier.database.session_manager import get_session_manager
from local_newsifier.crud.canonical_entity import canonical_entity as canonical_entity_crud
from local_newsifier.crud.entity import entity as entity_crud
from local_newsifier.crud.entity_mention_context import entity_mention_context as entity_mention_context_crud
from local_newsifier.crud.entity_profile import entity_profile as entity_profile_crud
from local_newsifier.models.database.entity import Entity
from local_newsifier.models.entity_tracking import (
    CanonicalEntity, EntityMentionContext, EntityProfile
)


class EntityService:
    """Service for entity-related business logic."""

    def __init__(self, session_manager=None):
        """Initialize the entity service.

        Args:
            session_manager: Session manager for database access (optional)
        """
        self.session_manager = session_manager or get_session_manager()

    def resolve_entity(self, name: str, entity_type: str, similarity_threshold: float = 0.85) -> Dict[str, Any]:
        """Resolve an entity name to its canonical form.

        Args:
            name: Entity name to resolve
            entity_type: Type of entity (e.g., 'PERSON', 'ORG')
            similarity_threshold: Threshold for entity name similarity (0.0 to 1.0)

        Returns:
            Dictionary with canonical entity information
        """
        with self.session_manager.session() as session:
            # This is a simplified version - in the real implementation, we would
            # use the EntityResolver but without creating a circular dependency
            canonical = canonical_entity_crud.get_by_name(
                session, name=name, entity_type=entity_type
            )
            
            if not canonical:
                # Create new canonical entity if none exists
                canonical_data = CanonicalEntity(
                    name=name,
                    entity_type=entity_type
                )
                canonical = canonical_entity_crud.create(session, obj_in=canonical_data)
                
            return canonical.dict()

    def track_entity(
        self,
        article_id: int,
        entity_text: str,
        entity_type: str,
        context_text: str,
        sentiment_score: float,
        framing_category: str,
        published_at: datetime
    ) -> Dict[str, Any]:
        """Track an entity mention in an article.

        Args:
            article_id: ID of the article containing the entity
            entity_text: Original entity text
            entity_type: Type of entity (e.g., 'PERSON', 'ORG')
            context_text: Context text surrounding the entity mention
            sentiment_score: Sentiment score for the context
            framing_category: Framing category for the context
            published_at: Publication date of the article

        Returns:
            Dictionary with entity tracking information
        """
        with self.session_manager.session() as session:
            # First resolve to canonical entity
            canonical_entity_dict = self.resolve_entity(entity_text, entity_type)
            canonical_entity_id = canonical_entity_dict["id"]
            
            # Store entity
            entity_data = Entity(
                article_id=article_id,
                text=entity_text,
                entity_type=entity_type,
                confidence=1.0
            )
            entity = entity_crud.create(session, obj_in=entity_data)
            
            # Store entity mention context
            context_data = EntityMentionContext(
                entity_id=entity.id,
                article_id=article_id,
                context_text=context_text,
                context_type="sentence",
                sentiment_score=sentiment_score
            )
            entity_mention_context_crud.create(session, obj_in=context_data)
            
            # Update entity profile
            self._update_entity_profile(
                session=session,
                canonical_entity_id=canonical_entity_id,
                entity_text=entity_text,
                context_text=context_text,
                sentiment_score=sentiment_score,
                framing_category=framing_category,
                published_at=published_at
            )
            
            return {
                "entity_id": entity.id,
                "canonical_entity_id": canonical_entity_id,
                "original_text": entity_text,
                "canonical_name": canonical_entity_dict["name"],
                "context": context_text
            }

    def _update_entity_profile(
        self,
        session: Session,
        canonical_entity_id: int,
        entity_text: str,
        context_text: str,
        sentiment_score: float,
        framing_category: str,
        published_at: datetime
    ) -> None:
        """Update entity profile with new mention data.

        Args:
            session: Database session
            canonical_entity_id: ID of the canonical entity
            entity_text: Original entity text
            context_text: Context text for the entity mention
            sentiment_score: Sentiment score for the context
            framing_category: Framing category for the context
            published_at: Publication date of the article
        """
        # Get existing profile or create new one
        current_profile = entity_profile_crud.get_by_entity(session, entity_id=canonical_entity_id)

        if current_profile:
            # Get existing metadata or create new
            metadata = current_profile.profile_metadata or {}
            mention_count = metadata.get("mention_count", 0) + 1

            # Get existing temporal data or create new
            temporal_data = metadata.get("temporal_data", {})
            date_key = published_at.strftime("%Y-%m-%d")
            if date_key in temporal_data:
                temporal_data[date_key] += 1
            else:
                temporal_data[date_key] = 1

            # Update contexts (keep only a sample)
            contexts = metadata.get("contexts", [])
            if len(contexts) < 10:  # Limit to 10 sample contexts
                contexts.append(context_text)

            # Update profile
            profile_data = EntityProfile(
                canonical_entity_id=canonical_entity_id,
                profile_type="summary",
                content=f"Entity {entity_text} has been mentioned {mention_count} times.",
                profile_metadata={
                    "mention_count": mention_count,
                    "contexts": contexts,
                    "temporal_data": temporal_data,
                    "sentiment_scores": {
                        "latest": sentiment_score,
                        "average": ((
                            current_profile.profile_metadata["sentiment_scores"]["average"]
                            if current_profile.profile_metadata and "sentiment_scores" in current_profile.profile_metadata
                            else sentiment_score
                        ) + sentiment_score) / 2
                    },
                    "framing_categories": {
                        "latest": framing_category,
                        "history": (
                            current_profile.profile_metadata["framing_categories"]["history"]
                            if current_profile.profile_metadata and "framing_categories" in current_profile.profile_metadata
                            else []
                        ) + [framing_category]
                    }
                }
            )
            
            entity_profile_crud.update_or_create(session, obj_in=profile_data)
        else:
            # Create new profile
            profile_data = EntityProfile(
                canonical_entity_id=canonical_entity_id,
                profile_type="summary",
                content=f"Entity {entity_text} has been mentioned once.",
                profile_metadata={
                    "mention_count": 1,
                    "contexts": [context_text],
                    "temporal_data": {published_at.strftime("%Y-%m-%d"): 1},
                    "sentiment_scores": {
                        "latest": sentiment_score,
                        "average": sentiment_score
                    },
                    "framing_categories": {
                        "latest": framing_category,
                        "history": [framing_category]
                    }
                }
            )
            
            entity_profile_crud.create(session, obj_in=profile_data)

    def get_entity_timeline(
        self,
        entity_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """Get timeline of mentions for a specific entity.

        Args:
            entity_id: ID of the canonical entity
            start_date: Start date for the timeline
            end_date: End date for the timeline

        Returns:
            List of mentions with article details
        """
        with self.session_manager.session() as session:
            return canonical_entity_crud.get_entity_timeline(
                session, entity_id=entity_id, start_date=start_date, end_date=end_date
            )

    def get_entity_sentiment_trend(
        self,
        entity_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """Get sentiment trend for a specific entity over time.

        Args:
            entity_id: ID of the canonical entity
            start_date: Start date for the trend
            end_date: End date for the trend

        Returns:
            List of sentiment scores by date
        """
        with self.session_manager.session() as session:
            return entity_mention_context_crud.get_sentiment_trend(
                session, entity_id=entity_id, start_date=start_date, end_date=end_date
            )
