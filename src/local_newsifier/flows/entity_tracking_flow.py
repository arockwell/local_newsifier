"""Flow for tracking entities across news articles."""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from crewai import Flow

from ..database.manager import DatabaseManager
from ..models.database import Article, ArticleDB
from ..models.entity_tracking import CanonicalEntity
from ..models.state import AnalysisStatus, NewsAnalysisState
from ..tools.entity_tracker import EntityTracker


class EntityTrackingFlow(Flow):
    """Flow for tracking person entities across news articles."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize the entity tracking flow."""
        super().__init__()
        self.db_manager = db_manager
        self.entity_tracker = EntityTracker(db_manager)
    
    def process_new_articles(self) -> List[Dict]:
        """
        Process all new articles for entity tracking.
        
        Returns:
            List of processed articles with entity counts
        """
        # Get articles with status "scraped" or "analyzed" that haven't been processed for entities
        articles = self.db_manager.get_articles_by_status("analyzed")
        
        results = []
        for article in articles:
            # Process article
            processed = self.process_article(article.id)
            
            # Update article status to indicate entity tracking is complete
            self.db_manager.update_article_status(article.id, "entity_tracked")
            
            # Add to results
            results.append({
                "article_id": article.id,
                "title": article.title,
                "url": article.url,
                "entity_count": len(processed),
                "entities": processed
            })
        
        return results
    
    def process_article(self, article_id: int) -> List[Dict]:
        """
        Process a single article for entity tracking.
        
        Args:
            article_id: ID of the article to process
            
        Returns:
            List of processed entity mentions
        """
        # Get article
        article = self.db_manager.get_article(article_id)
        if not article:
            raise ValueError(f"Article with ID {article_id} not found")
        
        # Process article content
        processed_entities = self.entity_tracker.process_article(
            article_id=article.id,
            content=article.content,
            title=article.title,
            published_at=article.published_at or datetime.utcnow()
        )
        
        return processed_entities
    
    def get_entity_dashboard(
        self, 
        days: int = 30, 
        entity_type: str = "PERSON"
    ) -> Dict:
        """
        Generate entity tracking dashboard data.
        
        Args:
            days: Number of days to include in the dashboard
            entity_type: Type of entities to include
            
        Returns:
            Dashboard data with entity statistics
        """
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Get all canonical entities of the specified type
        entities = self.db_manager.get_canonical_entities_by_type(entity_type)
        
        # Get mention counts and trends for each entity
        entity_data = []
        for entity in entities:
            # Get mention count
            mention_count = self.db_manager.get_entity_mentions_count(entity.id)
            
            # Get mention timeline
            timeline = self.db_manager.get_entity_timeline(
                entity.id, start_date, end_date
            )
            
            # Get sentiment trend
            sentiment_trend = self.db_manager.get_entity_sentiment_trend(
                entity.id, start_date, end_date
            )
            
            # Add to entity data
            entity_data.append({
                "id": entity.id,
                "name": entity.name,
                "type": entity.entity_type,
                "mention_count": mention_count,
                "first_seen": entity.first_seen,
                "last_seen": entity.last_seen,
                "timeline": timeline[:5],  # Include only 5 most recent mentions
                "sentiment_trend": sentiment_trend
            })
        
        # Sort entities by mention count (descending)
        entity_data.sort(key=lambda x: x["mention_count"], reverse=True)
        
        # Prepare dashboard data
        dashboard = {
            "date_range": {
                "start": start_date,
                "end": end_date,
                "days": days
            },
            "entity_count": len(entity_data),
            "total_mentions": sum(e["mention_count"] for e in entity_data),
            "entities": entity_data[:20],  # Include only top 20 entities
        }
        
        return dashboard
    
    def find_entity_relationships(
        self, 
        entity_id: int, 
        days: int = 30
    ) -> Dict:
        """
        Find relationships between entities based on co-occurrence.
        
        Args:
            entity_id: ID of the canonical entity
            days: Number of days to include
            
        Returns:
            Entity relationships data
        """
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Get entity name
        entity = self.db_manager.get_canonical_entity(entity_id)
        if not entity:
            raise ValueError(f"Entity with ID {entity_id} not found")
        
        # Get articles mentioning this entity
        articles = self.db_manager.get_articles_mentioning_entity(entity_id, start_date, end_date)
        
        # Find co-occurring entities
        co_occurrences = {}
        for article in articles:
            # Get all entities mentioned in this article
            article_entities = self.db_manager.get_entities_by_article(article.id)
            
            # Get canonical entities for these mentions
            for article_entity in article_entities:
                # Skip if this is the same entity we're analyzing
                if article_entity.text == entity.name:
                    continue
                
                # Resolve to canonical entity
                canonical_entity = self.entity_tracker.entity_resolver.resolve_entity(article_entity.text)
                
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
                        "articles": {article.id}
                    }
        
        # Convert to list and sort by co-occurrence count
        relationships = []
        for entity_id, data in co_occurrences.items():
            relationships.append({
                "entity_id": entity_id,
                "entity_name": data["entity"].name,
                "entity_type": data["entity"].entity_type,
                "co_occurrence_count": data["count"],
                "article_count": len(data["articles"])
            })
        
        relationships.sort(key=lambda x: x["co_occurrence_count"], reverse=True)
        
        return {
            "entity_id": entity_id,
            "entity_name": entity.name,
            "date_range": {
                "start": start_date,
                "end": end_date,
                "days": days
            },
            "relationships": relationships[:20]  # Include only top 20 relationships
        }