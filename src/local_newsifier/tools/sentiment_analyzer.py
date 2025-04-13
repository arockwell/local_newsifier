"""Tool for performing sentiment analysis on news article content."""

import logging
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any

import spacy
from spacy.language import Language
from sqlalchemy.orm import Session

from ..models.state import AnalysisStatus, NewsAnalysisState
from ..models.sentiment import SentimentAnalysisCreate
from ..database.manager import DatabaseManager

logger = logging.getLogger(__name__)


class SentimentAnalysisTool:
    """Tool for performing sentiment analysis using spaCy and other techniques."""

    def __init__(self, model_name: str = "en_core_web_lg"):
        """
        Initialize the sentiment analyzer.

        Args:
            model_name: Name of the spaCy model to use
        """
        try:
            self.nlp: Language = spacy.load(model_name)
        except OSError:
            logger.warning(
                f"spaCy model '{model_name}' not found. "
                f"Please install it using: python -m spacy download {model_name}"
            )
            self.nlp = None

        # Define simplified VADER-like lexicon for demonstration
        # In a production system, you'd use a more comprehensive lexicon or a pre-trained model
        self.sentiment_lexicon = {
            # Positive words
            "good": 1.0, "great": 1.5, "excellent": 2.0, "amazing": 2.0, 
            "wonderful": 1.8, "outstanding": 1.9, "fantastic": 1.9,
            "positive": 1.0, "praise": 1.2, "benefit": 0.8, "success": 1.0,
            # Negative words
            "bad": -1.0, "terrible": -1.8, "awful": -1.7, "horrible": -1.9,
            "poor": -1.2, "negative": -1.0, "failure": -1.5, "disaster": -1.8,
            "crisis": -1.6, "problem": -1.0, "issue": -0.7, "concern": -0.8,
            # Intensifiers
            "very": 0.3, "extremely": 0.6, "incredibly": 0.5,
            # Negations
            "not": -1.0, "no": -1.0, "never": -1.0, "without": -0.5,
        }
        
        # Negation detection pattern
        self.negation_pattern = re.compile(r'\b(?:not|no|never|none|nothing|nowhere|nobody|neither|nor)\b')

    def _analyze_text_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment of text using lexicon-based approach.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with sentiment score and magnitude
        """
        if not text:
            return {"sentiment": 0.0, "magnitude": 0.0}
        
        # Process the text with spaCy if available
        if self.nlp:
            doc = self.nlp(text)
            sentences = list(doc.sents)
        else:
            # Simple sentence splitting as fallback
            sentences = [sent.strip() for sent in re.split(r'[.!?]+', text) if sent.strip()]
        
        total_score = 0.0
        sentence_scores = []
        
        for sentence in sentences:
            sentence_text = str(sentence).lower()
            score = self._score_sentence(sentence_text)
            sentence_scores.append(score)
            total_score += score
        
        # Calculate document-level sentiment
        if sentences:
            avg_sentiment = total_score / len(sentences)
        else:
            avg_sentiment = 0.0
            
        # Calculate magnitude (strength of sentiment)
        magnitude = sum(abs(score) for score in sentence_scores)
        if sentences:
            magnitude /= len(sentences)
        
        return {
            "sentiment": avg_sentiment,
            "magnitude": magnitude,
            "sentence_count": len(sentences),
        }

    def _score_sentence(self, sentence: str) -> float:
        """
        Score a single sentence for sentiment.

        Args:
            sentence: Sentence text

        Returns:
            Sentiment score
        """
        words = re.findall(r'\b\w+\b', sentence.lower())
        
        if not words:
            return 0.0
        
        total_score = 0.0
        negation_active = False
        
        for i, word in enumerate(words):
            # Check for negation
            if self.negation_pattern.search(word):
                negation_active = True
                continue
                
            # Get sentiment from lexicon
            word_sentiment = self.sentiment_lexicon.get(word, 0.0)
            
            # Apply negation if active
            if negation_active and word_sentiment != 0.0:
                word_sentiment *= -0.7  # Partial reversal of sentiment
                negation_active = False  # Reset after applying
                
            # Reset negation if it wasn't used for next 3 words
            if negation_active and i > 0 and (i % 3 == 0):
                negation_active = False
                
            total_score += word_sentiment
            
        # Normalize by word count
        return total_score / len(words)

    def _extract_entity_sentiments(self, text: str, entities: List[Dict]) -> Dict[str, float]:
        """
        Extract sentiment scores for named entities.

        Args:
            text: Full text content
            entities: List of entity dictionaries with text and sentence

        Returns:
            Dictionary mapping entity text to sentiment score
        """
        entity_sentiments = {}
        
        for entity_type, entity_list in entities.items():
            for entity in entity_list:
                entity_text = entity["text"]
                sentence = entity["sentence"]
                
                # Skip if already processed this entity
                if entity_text in entity_sentiments:
                    continue
                
                # Analyze the sentence containing the entity
                sentiment_data = self._analyze_text_sentiment(sentence)
                entity_sentiments[entity_text] = sentiment_data["sentiment"]
                
        return entity_sentiments

    def _extract_topic_sentiments(self, text: str) -> Dict[str, float]:
        """
        Extract sentiment scores for key topics in the text.

        Args:
            text: Full text content

        Returns:
            Dictionary mapping topics to sentiment scores
        """
        topics = {}
        
        # Use spaCy for topic extraction if available
        if self.nlp:
            doc = self.nlp(text)
            
            # Extract noun phrases as potential topics
            for chunk in doc.noun_chunks:
                # Skip short or stop word chunks
                if len(chunk) <= 1 or all(token.is_stop for token in chunk):
                    continue
                    
                topic_text = chunk.text.lower()
                
                # Get the sentence containing this topic
                sentence = chunk.sent.text
                
                # Analyze sentiment of the sentence
                sentiment_data = self._analyze_text_sentiment(sentence)
                
                # Store or update sentiment for this topic
                if topic_text in topics:
                    # Average with existing sentiment
                    current = topics[topic_text]
                    count = topics.get(f"{topic_text}_count", 1)
                    topics[topic_text] = (current * count + sentiment_data["sentiment"]) / (count + 1)
                    topics[f"{topic_text}_count"] = count + 1
                else:
                    topics[topic_text] = sentiment_data["sentiment"]
                    topics[f"{topic_text}_count"] = 1
        
        # Clean up the counts
        clean_topics = {}
        for key, value in topics.items():
            if not key.endswith("_count"):
                clean_topics[key] = value
                
        return clean_topics

    def analyze(self, state: NewsAnalysisState) -> NewsAnalysisState:
        """
        Analyze article content for sentiment.

        Args:
            state: Current pipeline state

        Returns:
            Updated state
        """
        try:
            state.status = AnalysisStatus.ANALYZING
            state.add_log("Starting sentiment analysis")

            if not state.scraped_text:
                raise ValueError("No text content available for analysis")

            # Perform document-level sentiment analysis
            document_sentiment = self._analyze_text_sentiment(state.scraped_text)
            
            # Extract entity sentiments if we have entities from NER
            entity_sentiments = {}
            if state.analysis_results and "entities" in state.analysis_results:
                entity_sentiments = self._extract_entity_sentiments(
                    state.scraped_text, state.analysis_results["entities"]
                )
            
            # Extract topic sentiments
            topic_sentiments = self._extract_topic_sentiments(state.scraped_text)
            
            # Store results
            sentiment_results = {
                "document_sentiment": document_sentiment["sentiment"],
                "document_magnitude": document_sentiment["magnitude"],
                "entity_sentiments": entity_sentiments,
                "topic_sentiments": topic_sentiments,
            }
            
            # Update state
            if not state.analysis_results:
                state.analysis_results = {}
                
            state.analysis_results["sentiment"] = sentiment_results
            state.analyzed_at = datetime.now(timezone.utc)
            state.status = AnalysisStatus.ANALYSIS_SUCCEEDED
            state.add_log(
                f"Successfully completed sentiment analysis. "
                f"Document sentiment: {document_sentiment['sentiment']:.2f}"
            )

        except Exception as e:
            state.status = AnalysisStatus.ANALYSIS_FAILED
            state.set_error("analysis", e)
            state.add_log(f"Error during sentiment analysis: {str(e)}")
            raise

        return state
        
    def analyze_article(
        self, 
        db_manager: DatabaseManager, 
        article_id: int
    ) -> Dict[str, Any]:
        """
        Analyze sentiment for a specific article in the database.
        
        Args:
            db_manager: Database manager instance
            article_id: ID of the article to analyze
            
        Returns:
            Sentiment analysis results
        """
        # Get article from database
        article = db_manager.get_article(article_id)
        if not article:
            raise ValueError(f"Article with ID {article_id} not found")
            
        # Get existing analysis results
        analysis_results = db_manager.get_analysis_results_by_article(article_id)
        entities_result = next((r for r in analysis_results if r.analysis_type == "NER"), None)
        
        # Create a temporary state for analysis
        state = NewsAnalysisState(
            article_id=article_id,
            article_url=article.url,
            scraped_text=article.content,
            analysis_results={"entities": entities_result.results["entities"] if entities_result else {}}
        )
        
        # Perform sentiment analysis
        self.analyze(state)
        
        # Store sentiment analysis results in database
        sentiment_create = SentimentAnalysisCreate(
            article_id=article_id,
            document_sentiment=state.analysis_results["sentiment"]["document_sentiment"],
            document_magnitude=state.analysis_results["sentiment"]["document_magnitude"],
            entity_sentiments=state.analysis_results["sentiment"]["entity_sentiments"],
            topic_sentiments=state.analysis_results["sentiment"]["topic_sentiments"]
        )
        
        # Create analysis result record
        analysis_result = db_manager.add_analysis_result({
            "article_id": article_id,
            "analysis_type": "sentiment",
            "results": state.analysis_results["sentiment"]
        })
        
        return state.analysis_results["sentiment"]