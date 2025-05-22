"""Context analyzer tool for analyzing entity mention contexts."""

from typing import Annotated, Any, Dict, List, Optional

import spacy
from fastapi import Depends
from fastapi_injectable import injectable
from spacy.language import Language
from spacy.tokens import Doc, Span


@injectable(use_cache=False)
class ContextAnalyzer:
    """Tool for analyzing the context of entity mentions."""

    def __init__(
        self,
        nlp_model: Optional[Any] = None,
        model_name: str = "en_core_web_lg"
    ):
        """Initialize with spaCy model.

        Args:
            nlp_model: Pre-loaded spaCy NLP model (injected)
            model_name: Name of the spaCy model to use as fallback
        """
        self.nlp = nlp_model

        # Fallback to loading model if not injected (for backward compatibility)
        if self.nlp is None:
            try:
                self.nlp: Language = spacy.load(model_name)
            except OSError:
                self.nlp = None
            
        # Initialize sentiment lexicon
        self.sentiment_words = {
            "positive": [
                "good", "great", "excellent", "outstanding", "amazing", "wonderful",
                "praised", "successful", "acclaim", "admire", "innovative", "praise",
                "promising", "celebrated", "impressive", "accomplished", "respected",
                "trusted", "remarkable", "notable", "benefit", "improve", "advantage",
                "support", "positive", "progress", "lead", "achieve", "success"
            ],
            "negative": [
                "bad", "terrible", "poor", "awful", "horrible", "disappointing",
                "criticized", "controversial", "scandal", "failed", "failure", "problem",
                "issue", "concern", "criticized", "accused", "alleged", "questionable",
                "troubled", "negative", "oppose", "against", "reject", "dispute",
                "contradict", "deny", "refuse", "blame", "attack", "criticism"
            ]
        }
        
        # Framing categories and related terms
        self.framing_categories = {
            "leadership": [
                "lead", "leader", "leadership", "direct", "guide", "manage", "executive",
                "vision", "strategy", "authority", "command", "influence", "inspire"
            ],
            "victim": [
                "victim", "suffer", "hurt", "harm", "damage", "affected", "vulnerable",
                "subjected", "targeted", "injured", "harmed", "impacted"
            ],
            "controversy": [
                "controversy", "controversial", "dispute", "argument", "debate", "conflict",
                "contentious", "divisive", "polarizing", "contested", "disagreement"
            ],
            "expert": [
                "expert", "expertise", "specialist", "authority", "knowledgeable", "professional",
                "experienced", "qualified", "skilled", "proficient", "competent", "master"
            ],
            "achievement": [
                "achieve", "success", "accomplish", "attain", "win", "victory", "triumph",
                "milestone", "breakthrough", "advancement", "progress", "achievement"
            ]
        }
    
    def analyze_sentiment(self, context: str) -> Dict[str, Any]:
        """
        Analyze sentiment in entity mention context.
        
        Args:
            context: Context text around entity mention
            
        Returns:
            Sentiment analysis results with score
        """
        if not self.nlp:
            return {
                "score": 0.0,
                "category": "neutral",
                "positive_count": 0,
                "negative_count": 0,
                "total_count": 0
            }
            
        doc = self.nlp(context.lower())
        
        # Count sentiment words
        positive_count = sum(1 for token in doc if token.lemma_ in self.sentiment_words["positive"])
        negative_count = sum(1 for token in doc if token.lemma_ in self.sentiment_words["negative"])
        
        # Calculate sentiment score (-1.0 to 1.0)
        total_count = positive_count + negative_count
        if total_count == 0:
            sentiment_score = 0.0
            sentiment_category = "neutral"
        else:
            sentiment_score = (positive_count - negative_count) / total_count
            if sentiment_score > 0.2:
                sentiment_category = "positive"
            elif sentiment_score < -0.2:
                sentiment_category = "negative"
            else:
                sentiment_category = "neutral"
        
        return {
            "score": sentiment_score,
            "category": sentiment_category,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "total_count": total_count
        }
    
    def analyze_framing(self, context: str) -> Dict[str, Any]:
        """
        Analyze framing of entity in mention context.
        
        Args:
            context: Context text around entity mention
            
        Returns:
            Framing analysis results with category scores
        """
        if not self.nlp:
            return {
                "category": "neutral",
                "scores": {},
                "counts": {},
                "total_count": 0
            }
            
        doc = self.nlp(context.lower())
        
        # Count framing-related words for each category
        framing_counts = {category: 0 for category in self.framing_categories}
        
        for token in doc:
            for category, words in self.framing_categories.items():
                if token.lemma_ in words:
                    framing_counts[category] += 1
        
        # Find dominant framing category
        dominant_category = max(framing_counts.items(), key=lambda x: x[1]) if any(framing_counts.values()) else ("neutral", 0)
        
        # Calculate framing scores (normalized)
        total_count = sum(framing_counts.values())
        framing_scores = {
            category: count / total_count if total_count > 0 else 0.0
            for category, count in framing_counts.items()
        }
        
        return {
            "category": dominant_category[0] if dominant_category[1] > 0 else "neutral",
            "scores": framing_scores,
            "counts": framing_counts,
            "total_count": total_count
        }
    
    def analyze_context(self, context: str) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of entity mention context.
        
        Args:
            context: Context text around entity mention
            
        Returns:
            Complete context analysis results
        """
        sentiment = self.analyze_sentiment(context)
        framing = self.analyze_framing(context)
        
        return {
            "sentiment": sentiment,
            "framing": framing,
            "length": len(context),
            "word_count": len(context.split())
        }
    
    def analyze_entity_contexts(
        self, 
        entities: List[Dict]
    ) -> List[Dict]:
        """
        Analyze contexts for multiple entities.
        
        Args:
            entities: List of entity dictionaries with 'context' field
            
        Returns:
            Entities with added context analysis
        """
        analyzed_entities = []
        
        for entity in entities:
            if "context" in entity:
                context_analysis = self.analyze_context(entity["context"])
                
                # Create a new entity dict with analysis added
                analyzed_entity = entity.copy()
                analyzed_entity["context_analysis"] = context_analysis
                
                analyzed_entities.append(analyzed_entity)
            else:
                # If no context, just pass through the entity
                analyzed_entities.append(entity)
                
        return analyzed_entities
    
    def get_sentiment_category(self, sentiment_score: float) -> str:
        """
        Get sentiment category from score.
        
        Args:
            sentiment_score: Sentiment score (-1.0 to 1.0)
            
        Returns:
            Sentiment category (positive, negative, neutral)
        """
        if sentiment_score > 0.2:
            return "positive"
        elif sentiment_score < -0.2:
            return "negative"
        else:
            return "neutral"
