"""Context analyzer tool for analyzing entity mention contexts."""

import re
from typing import Dict, List, Tuple

import spacy
from spacy.language import Language
from spacy.tokens import Doc, Span


class ContextAnalyzer:
    """Tool for analyzing entity mention contexts."""

    def __init__(self, model_name: str = "en_core_web_lg"):
        """
        Initialize the context analyzer.

        Args:
            model_name: Name of the spaCy model to use
        """
        try:
            self.nlp: Language = spacy.load(model_name)
        except OSError:
            raise RuntimeError(
                f"spaCy model '{model_name}' not found. "
                f"Please install it using: python -m spacy download {model_name}"
            )
        
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
    
    def extract_context(self, text: str, entity_text: str, window: int = 2) -> str:
        """
        Extract the context around an entity mention.
        
        Args:
            text: Full article text
            entity_text: The entity text to find
            window: Number of sentences before and after to include
            
        Returns:
            Context text around entity mention
        """
        doc = self.nlp(text)
        
        # Find all mentions of the entity
        mentions = []
        for sent_idx, sent in enumerate(doc.sents):
            if entity_text.lower() in sent.text.lower():
                mentions.append(sent_idx)
        
        # If no mentions found, return empty string
        if not mentions:
            return ""
        
        # Use the first mention for context (could be modified to include all mentions)
        mention_idx = mentions[0]
        
        # Get sentences around the mention
        context_sents = []
        for i in range(max(0, mention_idx - window), min(len(list(doc.sents)), mention_idx + window + 1)):
            context_sents.append(list(doc.sents)[i].text)
        
        return " ".join(context_sents)
    
    def analyze_sentiment(self, context: str) -> Dict[str, float]:
        """
        Analyze sentiment in entity mention context.
        
        Args:
            context: Context text around entity mention
            
        Returns:
            Sentiment analysis results with score
        """
        doc = self.nlp(context.lower())
        
        # Count sentiment words
        positive_count = sum(1 for token in doc if token.lemma_ in self.sentiment_words["positive"])
        negative_count = sum(1 for token in doc if token.lemma_ in self.sentiment_words["negative"])
        
        # Calculate sentiment score (-1.0 to 1.0)
        total_count = positive_count + negative_count
        if total_count == 0:
            sentiment_score = 0.0
        else:
            sentiment_score = (positive_count - negative_count) / total_count
        
        return {
            "score": sentiment_score,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "total_count": total_count
        }
    
    def analyze_framing(self, context: str) -> Dict[str, float]:
        """
        Analyze framing of entity in mention context.
        
        Args:
            context: Context text around entity mention
            
        Returns:
            Framing analysis results with category scores
        """
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
    
    def analyze_context(self, context: str) -> Dict[str, Dict]:
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