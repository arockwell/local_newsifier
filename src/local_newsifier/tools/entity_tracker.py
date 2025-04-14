"""Entity tracking tool for tracking person entities across news articles."""

from datetime import datetime
from typing import Dict, List, Optional, Tuple

import spacy
from spacy.language import Language
from spacy.tokens import Doc, Span

from ..database.manager import DatabaseManager
from ..models.pydantic_models import ArticleCreate, EntityCreate, Entity
from ..models.entity_tracking import (
    CanonicalEntityCreate, EntityMentionContextCreate, EntityProfileCreate
)
from .entity_resolver import EntityResolver
from .context_analyzer import ContextAnalyzer


class EntityTracker:
    """Tool for tracking person entities across news articles."""

    def __init__(
        self, 
        db_manager: DatabaseManager, 
        model_name: str = "en_core_web_sm",
        similarity_threshold: float = 0.85
    ):
        """
        Initialize the entity tracker.

        Args:
            db_manager: Database manager instance
            model_name: Name of the spaCy model to use
            similarity_threshold: Threshold for entity name similarity (0.0 to 1.0)
        """
        self.db_manager = db_manager
        
        try:
            self.nlp: Language = spacy.load(model_name)
        except OSError:
            raise RuntimeError(
                f"spaCy model '{model_name}' not found. "
                f"Please install it using: python -m spacy download {model_name}"
            )
        
        self.entity_resolver = EntityResolver(db_manager, similarity_threshold)
        self.context_analyzer = ContextAnalyzer(model_name)
    
    def process_article(
        self, 
        article_id: int,
        content: str,
        title: str,
        published_at: datetime
    ) -> List[Dict]:
        """
        Process an article to track entity mentions.
        
        Args:
            article_id: ID of the article being processed
            content: Article content
            title: Article title
            published_at: Article publication date
            
        Returns:
            List of processed entity mentions
        """
        # Extract person entities
        doc = self.nlp(content)
        person_entities = [ent for ent in doc.ents if ent.label_ == "PERSON"]
        
        # Process and deduplicate entities
        processed_entities = []
        unique_canonical_ids = set()
        
        for entity in person_entities:
            # Extract context for the entity
            context_text = entity.sent.text
            
            # Resolve to canonical entity
            canonical_entity = self.entity_resolver.resolve_entity(entity.text, "PERSON")
            
            # Skip if we've already processed this canonical entity for this article
            if canonical_entity.id in unique_canonical_ids:
                continue
            
            unique_canonical_ids.add(canonical_entity.id)
            
            # Analyze context for sentiment and framing
            context_analysis = self.context_analyzer.analyze_context(context_text)
            
            # Store entity in database
            db_entity = self._store_entity(
                article_id=article_id,
                entity_text=entity.text,
                canonical_entity_id=canonical_entity.id,
                context_text=context_text,
                sentiment_score=context_analysis["sentiment"]["score"],
                published_at=published_at
            )
            
            # Update entity profile
            self._update_entity_profile(
                canonical_entity_id=canonical_entity.id,
                entity_text=entity.text,
                context_text=context_text,
                sentiment_score=context_analysis["sentiment"]["score"],
                framing_category=context_analysis["framing"]["category"],
                published_at=published_at
            )
            
            # Add to results
            processed_entities.append({
                "original_text": entity.text,
                "canonical_name": canonical_entity.name,
                "canonical_id": canonical_entity.id,
                "context": context_text,
                "sentiment_score": context_analysis["sentiment"]["score"],
                "framing_category": context_analysis["framing"]["category"]
            })
        
        return processed_entities
    
    def _store_entity(
        self,
        article_id: int,
        entity_text: str,
        canonical_entity_id: int,
        context_text: str,
        sentiment_score: float,
        published_at: datetime
    ) -> Entity:
        """
        Store entity and context information in the database.
        
        Args:
            article_id: ID of the article
            entity_text: Original entity text
            canonical_entity_id: ID of the canonical entity
            context_text: Context text for the entity mention
            sentiment_score: Sentiment score for the context
            published_at: Publication date of the article
            
        Returns:
            Created entity database object
        """
        # Store entity
        entity_data = EntityCreate(
            article_id=article_id,
            text=entity_text,
            entity_type="PERSON",
            confidence=1.0  # We could calculate this based on NER confidence
        )
        entity = self.db_manager.add_entity(entity_data)
        
        # Store entity mention context
        context_data = EntityMentionContextCreate(
            entity_id=entity.id,
            article_id=article_id,
            context_text=context_text,
            context_type="sentence",
            sentiment_score=sentiment_score
        )
        self.db_manager.add_entity_mention_context(context_data)
        
        # Add to entity mentions association table - this is handled in the DB manager
        # but would be implemented here if needed
        
        return entity
    
    def _update_entity_profile(
        self,
        canonical_entity_id: int,
        entity_text: str,
        context_text: str,
        sentiment_score: float,
        framing_category: str,
        published_at: datetime
    ) -> None:
        """
        Update entity profile with new mention data.
        
        Args:
            canonical_entity_id: ID of the canonical entity
            entity_text: Original entity text
            context_text: Context text for the entity mention
            sentiment_score: Sentiment score for the context
            framing_category: Framing category for the context
            published_at: Publication date of the article
        """
        # Get existing profile or create new one
        current_profile = self.db_manager.get_entity_profile(canonical_entity_id)
        
        if current_profile:
            # Update existing profile
            mention_count = current_profile.mention_count + 1
            
            # Get existing temporal data or create new
            temporal_data = current_profile.temporal_data or {}
            date_key = published_at.strftime("%Y-%m-%d")
            if date_key in temporal_data:
                temporal_data[date_key] += 1
            else:
                temporal_data[date_key] = 1
            
            # Update contexts (keep only a sample)
            contexts = current_profile.contexts or []
            if len(contexts) < 10:  # Limit to 10 sample contexts
                contexts.append(context_text)
            
            # Update profile
            profile_data = EntityProfileCreate(
                canonical_entity_id=canonical_entity_id,
                mention_count=mention_count,
                contexts=contexts,
                temporal_data=temporal_data,
                # Other fields would be updated here as needed
            )
            self.db_manager.add_entity_profile(profile_data)
        else:
            # Create new profile
            # Initialize temporal data
            temporal_data = {published_at.strftime("%Y-%m-%d"): 1}
            
            profile_data = EntityProfileCreate(
                canonical_entity_id=canonical_entity_id,
                mention_count=1,
                contexts=[context_text],
                temporal_data=temporal_data,
                # Initialize other fields as needed
            )
            self.db_manager.add_entity_profile(profile_data)
    
    def get_entity_timeline(
        self, 
        entity_id: int, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict]:
        """
        Get timeline of mentions for a specific entity.
        
        Args:
            entity_id: ID of the canonical entity
            start_date: Start date for the timeline
            end_date: End date for the timeline
            
        Returns:
            List of mentions with article details
        """
        return self.db_manager.get_entity_timeline(entity_id, start_date, end_date)
    
    def get_entity_sentiment_trend(
        self, 
        entity_id: int, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict]:
        """
        Get sentiment trend for a specific entity over time.
        
        Args:
            entity_id: ID of the canonical entity
            start_date: Start date for the trend
            end_date: End date for the trend
            
        Returns:
            List of sentiment scores by date
        """
        return self.db_manager.get_entity_sentiment_trend(entity_id, start_date, end_date)

    def get_entity_appearances(self, entity_name: str, limit: int = 10) -> List[Dict]:
        """
        Get appearances of an entity in articles.
        
        Args:
            entity_name: Name of the entity to search for
            limit: Maximum number of appearances to return
            
        Returns:
            List of entity appearances with context
        """
        # First resolve the entity name to a canonical entity
        canonical_entity = self.entity_resolver.find_matching_entity(entity_name)
        if not canonical_entity:
            return []
        
        # Get entity mentions from the database
        try:
            # This would normally query the database for mentions
            # For demo purposes, return some sample data
            return [
                {
                    "article_title": "Sample Article 1",
                    "context": f"Discussion about {entity_name} in local politics",
                    "date": datetime.now(),
                    "sentiment": 0.5
                },
                {
                    "article_title": "Sample Article 2",
                    "context": f"{entity_name} attended the city council meeting",
                    "date": datetime.now(),
                    "sentiment": 0.3
                }
            ][:limit]
        except Exception as e:
            print(f"Error getting entity appearances: {e}")
            return []

    def get_entity_connections(self, entity_name: str, limit: int = 10) -> List[Dict]:
        """
        Get connections between entities in articles.
        
        Args:
            entity_name: Name of the entity to find connections for
            limit: Maximum number of connections to return
            
        Returns:
            List of entity connections with context
        """
        try:
            # This would normally query the database for connections
            # For demo purposes, return some sample data
            return [
                {
                    "source_entity": entity_name,
                    "target_entity": "Commissioner Smith",
                    "relationship_type": "colleague",
                    "strength": 0.8,
                    "context": "Both attended city council meetings"
                },
                {
                    "source_entity": entity_name,
                    "target_entity": "Local Business Association",
                    "relationship_type": "member",
                    "strength": 0.6,
                    "context": "Participated in business development initiatives"
                }
            ][:limit]
        except Exception as e:
            print(f"Error getting entity connections: {e}")
            return []