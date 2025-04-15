"""Entity tracking tool for tracking person entities across news articles."""

from datetime import datetime
from typing import Dict, List, Optional, Tuple

import spacy
from spacy.language import Language
from spacy.tokens import Doc, Span
from sqlmodel import Session

from ..models.article import Article
from ..models.entity import Entity
from ..models.entity_tracking import (
    CanonicalEntityCreate, EntityMentionContextCreate, EntityProfileCreate
)
from ..crud.article import create_article
from .entity_resolver import EntityResolver
from .context_analyzer import ContextAnalyzer


class EntityTracker:
    """Tool for tracking person entities across news articles."""

    def __init__(
        self, 
        session: Session, 
        model_name: str = "en_core_web_lg",
        similarity_threshold: float = 0.85
    ):
        """
        Initialize the entity tracker.

        Args:
            session: Database session
            model_name: Name of the spaCy model to use
            similarity_threshold: Threshold for entity name similarity (0.0 to 1.0)
        """
        self.session = session
        
        try:
            self.nlp: Language = spacy.load(model_name)
        except OSError:
            raise RuntimeError(
                f"spaCy model '{model_name}' not found. "
                f"Please install it using: python -m spacy download {model_name}"
            )
        
        self.entity_resolver = EntityResolver(session, similarity_threshold)
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
        # Create entity using SQLModel with updated schema
        entity = Entity(
            article_id=article_id,
            text=entity_text,
            entity_type="PERSON",
            confidence=1.0,  # We could calculate this based on NER confidence
            sentence_context=context_text
        )
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        
        # Store entity mention context
        context_data = EntityMentionContextCreate(
            entity_id=entity.id,
            article_id=article_id,
            context_text=context_text,
            context_type="sentence",
            sentiment_score=sentiment_score
        )
        
        # This would need to be implemented with SQLModel as well, but for now
        # we'll keep the original EntityMentionContextCreate model
        from ..models.entity_tracking import EntityMentionContextDB
        context = EntityMentionContextDB(**context_data.model_dump())
        self.session.add(context)
        self.session.commit()
        
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
        # Get existing profile or create new one using SQLModel
        from sqlmodel import select
        from ..models.entity_tracking import EntityProfileDB
        
        statement = select(EntityProfileDB).where(
            EntityProfileDB.canonical_entity_id == canonical_entity_id
        )
        current_profile = self.session.exec(statement).first()

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

            # Update profile using SQLModel
            updated_metadata = {
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
            
            # Update directly in SQLModel
            current_profile.content = f"Entity {entity_text} has been mentioned {mention_count} times."
            current_profile.profile_metadata = updated_metadata
            self.session.add(current_profile)
            self.session.commit()
        else:
            # Create new profile using SQLModel directly
            from ..models.entity_tracking import EntityProfileDB
            
            new_profile = EntityProfileDB(
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
            self.session.add(new_profile)
            self.session.commit()
    
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
        # This would be implemented with SQLModel's select statements
        # For now, we'll return a placeholder
        from sqlmodel import select, func
        from ..models.article import Article
        from ..models.entity_tracking import entity_mentions
        
        results = (
            self.session.query(
                Article.published_at,
                func.count(entity_mentions.c.id).label("mention_count"),
            )
            .join(entity_mentions, Article.id == entity_mentions.c.article_id)
            .filter(
                entity_mentions.c.canonical_entity_id == entity_id,
                Article.published_at >= start_date,
                Article.published_at <= end_date,
            )
            .group_by(Article.published_at)
            .order_by(Article.published_at)
            .all()
        )
        
        return [
            {
                "date": date,
                "mention_count": count,
            }
            for date, count in results
        ]
    
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
        # This would be implemented with SQLModel's select statements
        from sqlmodel import select, func
        from ..models.article import Article
        from ..models.entity_tracking import entity_mentions, EntityMentionContextDB
        
        results = (
            self.session.query(
                Article.published_at,
                func.avg(EntityMentionContextDB.sentiment_score).label("avg_sentiment"),
            )
            .join(entity_mentions, Article.id == entity_mentions.c.article_id)
            .join(
                EntityMentionContextDB,
                EntityMentionContextDB.entity_id == entity_mentions.c.entity_id,
            )
            .filter(
                entity_mentions.c.canonical_entity_id == entity_id,
                Article.published_at >= start_date,
                Article.published_at <= end_date,
            )
            .group_by(Article.published_at)
            .order_by(Article.published_at)
            .all()
        )
        
        return [
            {
                "date": date,
                "avg_sentiment": float(sentiment) if sentiment is not None else None,
            }
            for date, sentiment in results
        ]