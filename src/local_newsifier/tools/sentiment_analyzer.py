"""Tool for performing sentiment analysis on news article content."""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union, NamedTuple, TypedDict, TypeVar, cast

import spacy
from spacy.language import Language
from sqlalchemy.orm import Session
from textblob import TextBlob
from textblob.blob import BaseBlob, Blobber

from ..database.adapter import with_session, get_article, add_analysis_result
from ..models.database import ArticleDB
from ..models.pydantic_models import Article, AnalysisResult, AnalysisResultCreate
from ..models.sentiment import (
    SentimentAnalysis,
    SentimentAnalysisCreate,
    SentimentAnalysisResult,
    SentimentAnalysisResultCreate
)
from ..models.state import AnalysisStatus, NewsAnalysisState

logger = logging.getLogger(__name__)


class SentimentScore(TypedDict):
    """Type definition for sentiment scores."""
    polarity: float
    subjectivity: float


class AnalysisResults(TypedDict, total=False):
    sentiment: Dict[str, float]
    entities: Dict[str, Any]
    topics: Dict[str, Any]


class SentimentAnalysisError(Exception):
    """Base exception class for sentiment analysis errors."""
    pass


class EntitySentimentError(SentimentAnalysisError):
    """Exception class for entity sentiment extraction errors."""
    pass


class SentimentAnalysisTool:
    """Tool for performing sentiment analysis on news article content."""

    def __init__(self, session: Optional[Session] = None):
        """Initialize the sentiment analysis tool with required models.
        
        Args:
            session: Optional SQLAlchemy session for database access
        """
        self.nlp = spacy.load("en_core_web_sm")
        self.session = session
        logger.info("Initialized SentimentAnalysisTool with spaCy model")

    def _analyze_text_sentiment(self, text: str) -> SentimentScore:
        """Analyze sentiment of a text segment.

        Args:
            text: Text to analyze

        Returns:
            Dictionary containing sentiment scores
        """
        blob = TextBlob(text)
        # Cast sentiment to Any to avoid type checking issues with cached_property
        sentiment = cast(Any, blob.sentiment)
        return {
            "polarity": float(sentiment.polarity),
            "subjectivity": float(sentiment.subjectivity)
        }

    def _extract_entity_sentiments(
        self, text: str, entities: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, float]:
        """
        Extract sentiment scores for named entities.

        Args:
            text: Full text content
            entities: Dictionary mapping entity types to lists of entity dictionaries

        Returns:
            Dictionary mapping entity text to sentiment score
        """
        entity_sentiments = {}

        for entity_type, entity_list in entities.items():
            if not entity_list:  # Skip if entity_list is None or empty
                continue
                
            for entity in entity_list:
                if not entity:  # Skip if entity is None
                    continue
                    
                entity_text = entity.get("text", "")
                sentence = entity.get("sentence", "")

                # Skip if already processed this entity or missing data
                if not entity_text or not sentence or entity_text in entity_sentiments:
                    continue

                # Analyze the sentence containing the entity
                sentiment_data = self._analyze_text_sentiment(sentence)
                entity_sentiments[entity_text] = sentiment_data["polarity"]

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

                # Analyze sentiment of the sentence using TextBlob
                sentiment_data = self._analyze_text_sentiment(sentence)
                sentiment = sentiment_data["polarity"]

                # Store or update sentiment for this topic
                if topic_text in topics:
                    # Average with existing sentiment
                    current = topics[topic_text]
                    count = topics.get(f"{topic_text}_count", 1)
                    topics[topic_text] = (current * count + sentiment) / (count + 1)
                    topics[f"{topic_text}_count"] = count + 1
                else:
                    topics[topic_text] = sentiment

        return {k: v for k, v in topics.items() if not k.endswith("_count")}

    def analyze_sentiment(self, state: NewsAnalysisState) -> NewsAnalysisState:
        """Analyze sentiment for the article text and update the analysis state."""
        if not state.scraped_text:
            logger.warning("No text available for sentiment analysis")
            raise ValueError("No text content available for analysis")

        # Initialize sentiment results if not present
        if not state.analysis_results:
            state.analysis_results = {}
        if "sentiment" not in state.analysis_results:
            state.analysis_results["sentiment"] = {}

        # Analyze overall document sentiment
        sentiment_results = self._analyze_text_sentiment(state.scraped_text)
        state.analysis_results["sentiment"].update({
            "document_sentiment": sentiment_results["polarity"],
            "document_magnitude": sentiment_results["subjectivity"]
        })

        # Analyze entity sentiments if entities are present
        if "entities" in state.analysis_results:
            entity_sentiments = self._extract_entity_sentiments(
                state.scraped_text, 
                state.analysis_results["entities"]
            )
            state.analysis_results["sentiment"]["entity_sentiments"] = entity_sentiments

        # Analyze topic sentiments if topics are present
        if "topics" in state.analysis_results:
            topic_sentiments = self._extract_topic_sentiments(state.scraped_text)
            state.analysis_results["sentiment"]["topic_sentiments"] = topic_sentiments

        # Update state
        state.analyzed_at = datetime.now(timezone.utc)
        state.status = AnalysisStatus.ANALYSIS_SUCCEEDED
        state.add_log("Successfully completed sentiment analysis")

        return state

    @with_session
    def analyze_article(
        self, article_id: int, *, session: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Analyze sentiment of an article from the database.

        Args:
            article_id: ID of the article to analyze
            session: Optional SQLAlchemy session

        Returns:
            Dictionary containing sentiment analysis results
        """
        # Use provided session or instance session
        session = session or self.session
        
        # Get article from database
        article = get_article(article_id, session=session)
        if not article:
            raise ValueError(f"Article with ID {article_id} not found")

        # Create analysis state
        state = NewsAnalysisState(
            target_url=article.url,
            scraped_text=article.content,
            status=AnalysisStatus.INITIALIZED
        )

        # Analyze sentiment
        state = self.analyze_sentiment(state)

        # Ensure analysis_results exists and has sentiment
        if not state.analysis_results:
            return {}
        return state.analysis_results.get("sentiment", {})

    @with_session
    def analyze_article_sentiment(self, article_id: int, *, session: Optional[Session] = None) -> AnalysisResult:
        """
        Analyze sentiment of an article and save results to database.

        Args:
            article_id: ID of the article to analyze
            session: Optional SQLAlchemy session

        Returns:
            AnalysisResult containing the sentiment analysis
        """
        # Use provided session or instance session
        session = session or self.session
        
        # Get article from database
        article = get_article(article_id, session=session)
        if not article:
            raise ValueError(f"Article with ID {article_id} not found")

        # Analyze sentiment
        sentiment_results = self.analyze_article(article_id, session=session)

        # Create analysis result
        analysis_result = AnalysisResultCreate(
            article_id=article_id,
            analysis_type="sentiment",
            results=sentiment_results
        )

        return add_analysis_result(analysis_result, session=session)
