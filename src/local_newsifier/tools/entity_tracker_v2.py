"""Refactored entity tracking tool that uses the entity service."""

from datetime import datetime
from typing import Dict, List, Optional, Any

import spacy
from spacy.language import Language
from spacy.tokens import Doc, Span

from local_newsifier.database.session_manager import get_session_manager
from local_newsifier.services.entity_service import EntityService
from local_newsifier.tools.context_analyzer import ContextAnalyzer


class EntityTracker:
    """Tool for tracking person entities across news articles."""

    def __init__(
        self,
        entity_service=None,
        context_analyzer=None,
        session_manager=None,
        model_name: str = "en_core_web_lg",
        similarity_threshold: float = 0.85
    ):
        """Initialize the entity tracker with dependencies.

        Args:
            entity_service: Service for entity operations (optional)
            context_analyzer: Analyzer for context extraction (optional)
            session_manager: Session manager for database access (optional)
            model_name: Name of the spaCy model to use
            similarity_threshold: Threshold for entity name similarity (0.0 to 1.0)
        """
        self.session_manager = session_manager or get_session_manager()
        self.entity_service = entity_service or EntityService(session_manager=self.session_manager)
        
        try:
            self.nlp: Language = spacy.load(model_name)
        except OSError:
            raise RuntimeError(
                f"spaCy model '{model_name}' not found. "
                f"Please install it using: python -m spacy download {model_name}"
            )
        
        self.context_analyzer = context_analyzer or ContextAnalyzer(model_name)
        self.similarity_threshold = similarity_threshold
    
    def process_article(
        self, 
        article_id: int,
        content: str,
        title: str,
        published_at: datetime
    ) -> List[Dict]:
        """Process an article to track entity mentions.
        
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
            
            # Analyze context for sentiment and framing
            context_analysis = self.context_analyzer.analyze_context(context_text)
            
            # Track entity using the service
            entity_result = self.entity_service.track_entity(
                article_id=article_id,
                entity_text=entity.text,
                entity_type="PERSON",
                context_text=context_text,
                sentiment_score=context_analysis["sentiment"]["score"],
                framing_category=context_analysis["framing"]["category"],
                published_at=published_at
            )
            
            # Skip if we've already processed this canonical entity for this article
            canonical_id = entity_result["canonical_entity_id"]
            if canonical_id in unique_canonical_ids:
                continue
            
            unique_canonical_ids.add(canonical_id)
            
            # Add to results
            processed_entities.append({
                "original_text": entity.text,
                "canonical_name": entity_result["canonical_name"],
                "canonical_id": canonical_id,
                "context": context_text,
                "sentiment_score": context_analysis["sentiment"]["score"],
                "framing_category": context_analysis["framing"]["category"]
            })
        
        return processed_entities
    
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
        return self.entity_service.get_entity_timeline(
            entity_id=entity_id, 
            start_date=start_date, 
            end_date=end_date
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
        return self.entity_service.get_entity_sentiment_trend(
            entity_id=entity_id,
            start_date=start_date,
            end_date=end_date
        )
