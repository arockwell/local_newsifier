"""Flow for tracking entities across news articles."""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Union, Any

from crewai import Flow
from sqlmodel import Session

from local_newsifier.database.engine import with_session
from local_newsifier.crud.article import article as article_crud
from local_newsifier.crud.canonical_entity import canonical_entity as canonical_entity_crud
from local_newsifier.crud.entity import entity as entity_crud
from local_newsifier.crud.entity_mention_context import entity_mention_context as entity_mention_context_crud
from local_newsifier.models.database.article import Article
from local_newsifier.models.entity_tracking import CanonicalEntity
from local_newsifier.models.state import AnalysisStatus, NewsAnalysisState
from local_newsifier.tools.entity_tracker import EntityTracker


class EntityTrackingFlow(Flow):
    """Flow for tracking person entities across news articles."""

    def __init__(self, session: Optional[Session] = None):
        """Initialize the entity tracking flow.
        
        Args:
            session: SQLAlchemy session instance
        """
        super().__init__()
        self.session = session            
        self.entity_tracker = EntityTracker(session=session)

    @with_session
    def process_new_articles(self, *, session: Session = None) -> List[Dict]:
        """Process all new articles for entity tracking.

        Args:
            session: Database session

        Returns:
            List of processed articles with entity counts
        """
        # Use provided session if available, otherwise use the stored session
        if session is None and self.session is not None:
            session = self.session
            
        # Get articles with status "analyzed" that haven't been processed for entities
        articles = article_crud.get_by_status(session, status="analyzed")

        results = []
        for article in articles:
            # Process article
            processed = self.process_article(article.id, session=session)

            # Update article status to indicate entity tracking is complete
            article_crud.update_status(session, article_id=article.id, status="entity_tracked")

            # Add to results
            results.append(
                {
                    "article_id": article.id,
                    "title": article.title,
                    "url": article.url,
                    "entity_count": len(processed),
                    "entities": processed,
                }
            )

        return results

    @with_session
    def process_article(self, article_id: int, *, session: Session = None) -> List[Dict]:
        """Process a single article for entity tracking.

        Args:
            article_id: ID of the article to process
            session: Database session

        Returns:
            List of processed entity mentions
        """
        # Use provided session if available, otherwise use the stored session
        if session is None and self.session is not None:
            session = self.session
            
        # Get article
        article = article_crud.get(session, id=article_id)
            
        if not article:
            raise ValueError(f"Article with ID {article_id} not found")

        # Process article content
        processed_entities = self.entity_tracker.process_article(
            article_id=article.id,
            content=article.content,
            title=article.title,
            published_at=article.published_at or datetime.now(timezone.utc),
            session=session
        )

        return processed_entities

    @with_session
    def get_entity_dashboard(
        self, days: int = 30, entity_type: str = "PERSON", *, session: Session = None
    ) -> Dict:
        """Generate entity tracking dashboard data.

        Args:
            days: Number of days to include in the dashboard
            entity_type: Type of entities to include
            session: Database session

        Returns:
            Dashboard data with entity statistics
        """
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        # Use provided session if available, otherwise use the stored session
        if session is None and self.session is not None:
            session = self.session
            
        # Get all canonical entities of the specified type
        entities = canonical_entity_crud.get_by_type(session, entity_type=entity_type)

        # Get mention counts and trends for each entity
        entity_data = []
        for entity in entities:
            # Get mention count
            mention_count = canonical_entity_crud.get_mentions_count(session, entity_id=entity.id)
            timeline = canonical_entity_crud.get_entity_timeline(
                session, entity_id=entity.id, start_date=start_date, end_date=end_date
            )
            sentiment_trend = entity_mention_context_crud.get_sentiment_trend(
                session, entity_id=entity.id, start_date=start_date, end_date=end_date
            )

            # Add to entity data
            entity_data.append(
                {
                    "id": entity.id,
                    "name": entity.name,
                    "type": entity.entity_type,
                    "mention_count": mention_count,
                    "first_seen": entity.first_seen,
                    "last_seen": entity.last_seen,
                    "timeline": timeline[:5],  # Include only 5 most recent mentions
                    "sentiment_trend": sentiment_trend,
                }
            )

        # Sort entities by mention count (descending)
        entity_data.sort(key=lambda x: x["mention_count"], reverse=True)

        # Prepare dashboard data
        dashboard = {
            "date_range": {"start": start_date, "end": end_date, "days": days},
            "entity_count": len(entity_data),
            "total_mentions": sum(e["mention_count"] for e in entity_data),
            "entities": entity_data[:20],  # Include only top 20 entities
        }

        return dashboard

    @with_session
    def find_entity_relationships(
        self, entity_id: int, days: int = 30, *, session: Session = None
    ) -> Dict:
        """Find relationships between entities based on co-occurrence.

        Args:
            entity_id: ID of the canonical entity
            days: Number of days to include
            session: Database session

        Returns:
            Entity relationships data
        """
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        # Use provided session if available, otherwise use the stored session
        if session is None and self.session is not None:
            session = self.session
            
        # Get entity name and articles
        entity = canonical_entity_crud.get(session, id=entity_id)
        articles = canonical_entity_crud.get_articles_mentioning_entity(
            session, entity_id=entity_id, start_date=start_date, end_date=end_date
        )
            
        if not entity:
            raise ValueError(f"Entity with ID {entity_id} not found")

        # Find co-occurring entities
        co_occurrences = {}
        for article in articles:
            # Get all entities mentioned in this article
            article_entities = entity_crud.get_by_article(session, article_id=article.id)

            # Get canonical entities for these mentions
            for article_entity in article_entities:
                # Skip if this is the same entity we're analyzing
                if article_entity.text == entity.name:
                    continue

                # Resolve to canonical entity
                canonical_entity = self.entity_tracker.entity_resolver.resolve_entity(
                    article_entity.text, session=session
                )

                # Skip if this is still the same entity
                if canonical_entity.id == entity_id:
                    continue

                # Count co-occurrence
                if canonical_entity.id in co_occurrences:
                    co_occurrences[canonical_entity.id]["count"] += 1
                    co_occurrences[canonical_entity.id]["articles"].add(article.id)
                else:
                    co_occurrences[canonical_entity.id] = {
                        "entity": canonical_entity,
                        "count": 1,
                        "articles": {article.id},
                    }

        # Convert to list and sort by co-occurrence count
        relationships = []
        for related_id, data in co_occurrences.items():
            relationships.append(
                {
                    "entity_id": related_id,
                    "entity_name": data["entity"].name,
                    "entity_type": data["entity"].entity_type,
                    "co_occurrence_count": data["count"],
                    "article_count": len(data["articles"]),
                }
            )

        relationships.sort(key=lambda x: x["co_occurrence_count"], reverse=True)

        return {
            "entity_id": entity_id,
            "entity_name": entity.name,
            "date_range": {"start": start_date, "end": end_date, "days": days},
            "relationships": relationships[:20],  # Include only top 20 relationships
        }
