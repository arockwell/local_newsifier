"""Flow for tracking entities across news articles."""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Union, Any

from crewai import Flow
from sqlalchemy.orm import Session

from ..database.adapter import (
    get_article, 
    get_articles_by_status,
    update_article_status,
    get_canonical_entity,
    get_canonical_entities_by_type,
    get_entity_mentions_count,
    get_entity_timeline,
    get_entity_sentiment_trend,
    get_articles_mentioning_entity,
    get_entities_by_article,
    with_session
)
from ..models.database import ArticleDB
from ..models.entity_tracking import CanonicalEntity
from ..models.state import AnalysisStatus, NewsAnalysisState
from ..tools.entity_tracker import EntityTracker


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
        articles = get_articles_by_status("analyzed", session=session)

        results = []
        for article in articles:
            # Process article
            processed = self.process_article(article.id, session=session)

            # Update article status to indicate entity tracking is complete
            update_article_status(article.id, "entity_tracked", session=session)

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
        article = get_article(article_id, session=session)
            
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
        entities = get_canonical_entities_by_type(entity_type, session=session)

        # Get mention counts and trends for each entity
        entity_data = []
        for entity in entities:
            # Get mention count
            mention_count = get_entity_mentions_count(entity.id, session=session)
            timeline = get_entity_timeline(entity.id, start_date, end_date, session=session)
            sentiment_trend = get_entity_sentiment_trend(entity.id, start_date, end_date, session=session)

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
        entity = get_canonical_entity(entity_id, session=session)
        articles = get_articles_mentioning_entity(entity_id, start_date, end_date, session=session)
            
        if not entity:
            raise ValueError(f"Entity with ID {entity_id} not found")

        # Find co-occurring entities
        co_occurrences = {}
        for article in articles:
            # Get all entities mentioned in this article
            article_entities = get_entities_by_article(article.id, session=session)

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
