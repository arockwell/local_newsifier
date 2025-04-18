"""
Headline analysis tool for detecting trends in news headlines.

This module provides tools for analyzing news headlines over time to identify trending terms 
and topics. It offers functionality for:

1. Grouping headlines by time periods (day, week, month)
2. Extracting significant keywords using NLP or simple tokenization
3. Detecting trending terms by analyzing temporal patterns
4. Calculating growth rates for keywords over time
5. Generating trend analysis results in structured format

The HeadlineTrendAnalyzer is designed to work with the database to retrieve headline data
and perform analysis efficiently, even with large datasets.
"""

import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

import spacy
from sqlmodel import Session, select

from ...database.engine import with_session
from ...models.database.article import Article

logger = logging.getLogger(__name__)


class HeadlineTrendAnalyzer:
    """Tool for analyzing trends in article headlines over time."""

    def __init__(self, session: Optional[Session] = None, nlp_model: Optional[str] = "en_core_web_lg"):
        """
        Initialize the headline trend analyzer.
        
        Args:
            session: Optional SQLAlchemy session for database access
            nlp_model: Name of the spaCy model to use
        """
        self.session = session
        try:
            self.nlp = spacy.load(nlp_model)
        except OSError:
            logger.error(f"spaCy model '{nlp_model}' not found. Some NLP features will be disabled.")
            self.nlp = None

    @with_session
    def get_headlines_by_period(
        self, 
        start_date: datetime, 
        end_date: datetime, 
        interval: str = "day",
        *, 
        session: Optional[Session] = None
    ) -> Dict[str, List[str]]:
        """
        Retrieve headlines grouped by time period.
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            interval: Time interval for grouping ('day', 'week', 'month')
            session: Optional SQLAlchemy session
            
        Returns:
            Dictionary mapping time periods to lists of headlines
        """
        # Use provided session, instance session, or create new session
        session = session or self.session
        
        # Query all articles in the date range using SQLModel syntax
        statement = select(Article).where(
            Article.published_at >= start_date,
            Article.published_at <= end_date
        ).order_by(Article.published_at)
        articles = session.exec(statement).all()
        
        # Group by time interval
        grouped_headlines = defaultdict(list)
        for article in articles:
            if not article.title:
                continue
                
            interval_key = self._get_interval_key(article.published_at, interval)
            grouped_headlines[interval_key].append(article.title)
            
        return dict(grouped_headlines) # Convert defaultdict to regular dict to make test pass
    
    def extract_keywords(self, headlines: List[str], top_n: int = 50) -> List[Tuple[str, int]]:
        """
        Extract significant keywords from a collection of headlines.
        
        Args:
            headlines: List of headlines to analyze
            top_n: Number of top keywords to return
            
        Returns:
            List of (keyword, count) tuples sorted by frequency
        """
        if not headlines:
            return []
            
        if not self.nlp:
            # Fallback simple keyword extraction if NLP is unavailable
            words = []
            for headline in headlines:
                words.extend(headline.split())
            
            # Filter common words and count
            stopwords = {"the", "a", "an", "and", "in", "on", "at", "to", "for", "of", "with", "by"}
            filtered_words = [w.lower() for w in words if w.lower() not in stopwords and len(w) > 2]
            return Counter(filtered_words).most_common(top_n)
        
        # NLP-based keyword extraction
        combined_text = " ".join(headlines)
        doc = self.nlp(combined_text)
        
        # Extract significant noun phrases and named entities
        keywords = []
        for chunk in doc.noun_chunks:
            if not any(token.is_stop for token in chunk):
                keywords.append(chunk.text.lower())
                
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "ORG", "GPE", "EVENT"]:
                keywords.append(ent.text.lower())
                
        # Count frequencies and return top N
        return Counter(keywords).most_common(top_n)
    
    @with_session
    def analyze_trends(
        self, 
        start_date: datetime, 
        end_date: datetime, 
        time_interval: str = "day",
        top_n: int = 20,
        *,
        session: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Analyze headline trends over the specified time period.
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            time_interval: Time interval for grouping ('day', 'week', 'month')
            top_n: Number of top keywords to analyze per period
            session: Optional SQLAlchemy session
            
        Returns:
            Dictionary containing trend analysis results
        """
        # Fetch headlines grouped by time interval
        grouped_headlines = self.get_headlines_by_period(
            start_date, end_date, time_interval, session=session
        )
        
        if not grouped_headlines:
            logger.warning(f"No headlines found in the period {start_date} to {end_date}")
            return {"error": "No headlines found in the specified period"}
            
        # Extract keywords for each time interval
        trend_data = {}
        for interval, headlines in grouped_headlines.items():
            trend_data[interval] = self.extract_keywords(headlines, top_n=top_n)
            
        # Identify trending terms
        trending_terms = self._detect_trends(trend_data)
        
        # Calculate overall top terms
        all_headlines = []
        for headlines in grouped_headlines.values():
            all_headlines.extend(headlines)
            
        overall_top_terms = self.extract_keywords(all_headlines, top_n=top_n)
        
        return {
            "trending_terms": trending_terms,
            "overall_top_terms": overall_top_terms,
            "raw_data": trend_data,
            "period_counts": {period: len(headlines) for period, headlines in grouped_headlines.items()}
        }
    
    def _detect_trends(self, trend_data: Dict[str, List[Tuple[str, int]]]) -> List[Dict[str, Any]]:
        """
        Detect trending terms by analyzing frequency changes over time.
        
        Args:
            trend_data: Dictionary mapping time periods to keyword frequency lists
            
        Returns:
            List of trending terms with growth metrics
        """
        if not trend_data or len(trend_data) < 2:
            return []
            
        # Convert to sorted time periods
        periods = sorted(trend_data.keys())
        
        # Track term frequencies across periods
        term_frequencies = defaultdict(lambda: {period: 0 for period in periods})
        for period in periods:
            for term, count in trend_data[period]:
                term_frequencies[term][period] = count
        
        # Calculate growth for each term
        term_growth = []
        for term, period_counts in term_frequencies.items():
            if sum(period_counts.values()) < 3:  # Filter noise
                logger.debug(f"Skipping term '{term}' due to insufficient mentions")
                continue
                
            # Calculate growth rate
            first_period = periods[0]
            last_period = periods[-1]
            
            # Check if term appeared in both first and last period
            if period_counts[first_period] > 0 and period_counts[last_period] > 0:
                growth_rate = (period_counts[last_period] - period_counts[first_period]) / max(1, period_counts[first_period])
                
                # Only consider significant growth
                if growth_rate > 0.5 or period_counts[last_period] >= 3:
                    term_growth.append({
                        "term": term,
                        "growth_rate": growth_rate,
                        "first_count": period_counts[first_period],
                        "last_count": period_counts[last_period],
                        "total_mentions": sum(period_counts.values())
                    })
        
        # Sort by growth rate descending
        return sorted(term_growth, key=lambda x: (x["growth_rate"], x["total_mentions"]), reverse=True)
    
    def _get_interval_key(self, date: datetime, interval: str) -> str:
        """
        Convert date to appropriate interval key (day, week, month).
        
        Args:
            date: Date to convert
            interval: Time interval type
            
        Returns:
            String key representing the time interval
        """
        if interval == "day":
            return date.strftime("%Y-%m-%d")
        elif interval == "week":
            return f"{date.year}-W{date.isocalendar()[1]}"
        elif interval == "month":
            return date.strftime("%Y-%m")
        return date.strftime("%Y")