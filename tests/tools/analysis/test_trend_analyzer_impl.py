"""Implementation tests for TrendAnalyzer.

This file tests the implementation of TrendAnalyzer methods directly to improve code coverage.
"""

import os
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session, select

from local_newsifier.tools.analysis.trend_analyzer import TrendAnalyzer
from local_newsifier.models.article import Article
from local_newsifier.models.trend import (
    TrendAnalysis,
    TrendType,
    TrendEntity,
    TrendEvidenceItem,
    TrendStatus
)


class TestTrendAnalyzerImplementation:
    """Test the implementation of TrendAnalyzer directly."""

    @pytest.fixture
    def trend_analyzer(self):
        """Create a TrendAnalyzer instance."""
        return TrendAnalyzer()

    @pytest.fixture
    def sample_articles(self, db_session):
        """Create sample articles for trend analysis."""
        articles = []
        # Create articles with trending keywords
        for i in range(10):
            # Add some trending keywords to even-indexed articles
            if i % 2 == 0:
                content = (
                    "This article discusses the trending topics of artificial intelligence, "
                    "climate change, and renewable energy. These are important issues that "
                    "are frequently discussed in the news."
                )
            else:
                content = (
                    "This article is about various subjects including technology, "
                    "politics, and finance. It doesn't focus on any particular trend."
                )
                
            article = Article(
                title=f"Test Article {i} about {'trending topics' if i % 2 == 0 else 'regular news'}",
                content=content,
                url=f"https://example.com/article-{i}",
                source="test_source",
                status="processed",
                published_at=datetime.now(timezone.utc) - timedelta(days=i),
                scraped_at=datetime.now(timezone.utc)
            )
            db_session.add(article)
            db_session.commit()
            db_session.refresh(article)
            articles.append(article)
        return articles

    def test_extract_keywords(self, trend_analyzer):
        """Test keyword extraction from text."""
        # Test with single document
        text = (
            "Artificial intelligence and machine learning are transforming healthcare. "
            "Many research institutes are exploring AI applications in medicine."
        )
        
        keywords = trend_analyzer.extract_keywords(text)
        
        # Verify keywords were extracted
        assert isinstance(keywords, list)
        assert len(keywords) > 0
        
        # Test stopword removal
        assert "the" not in keywords
        assert "and" not in keywords
        
        # Test with multiple documents
        texts = [
            "AI and machine learning applications in healthcare",
            "New advances in AI for medical diagnosis",
            "Machine learning models help doctors analyze data"
        ]
        
        keywords_list = trend_analyzer.extract_keywords(texts)
        
        # Verify keywords were extracted for multiple documents
        assert isinstance(keywords_list, list)
        assert len(keywords_list) > 0

    def test_extract_ngrams(self, trend_analyzer):
        """Test n-gram extraction."""
        text = "Artificial intelligence and machine learning are transforming healthcare"
        
        # Test unigrams
        unigrams = trend_analyzer.extract_ngrams(text, n=1)
        assert isinstance(unigrams, list)
        assert "artificial" in unigrams
        assert "intelligence" in unigrams
        
        # Test bigrams
        bigrams = trend_analyzer.extract_ngrams(text, n=2)
        assert isinstance(bigrams, list)
        assert "artificial intelligence" in bigrams
        assert "machine learning" in bigrams
        
        # Test trigrams
        trigrams = trend_analyzer.extract_ngrams(text, n=3)
        assert isinstance(trigrams, list)

    def test_normalize_text(self, trend_analyzer):
        """Test text normalization."""
        text = "Artificial Intelligence and Machine LEARNING are transforming HEALTHCARE!"
        
        normalized = trend_analyzer.normalize_text(text)
        
        # Verify normalization
        assert normalized == "artificial intelligence and machine learning are transforming healthcare"
        
        # Test with empty string
        assert trend_analyzer.normalize_text("") == ""
        
        # Test with None
        assert trend_analyzer.normalize_text(None) == ""

    def test_remove_stopwords(self, trend_analyzer):
        """Test stopword removal."""
        text = "the quick brown fox jumps over the lazy dog"
        words = text.split()
        
        filtered = trend_analyzer.remove_stopwords(words)
        
        # Verify stopwords were removed
        assert "the" not in filtered
        assert "over" not in filtered
        
        # Verify non-stopwords were kept
        assert "quick" in filtered
        assert "brown" in filtered
        assert "fox" in filtered

    def test_calculate_frequency(self, trend_analyzer):
        """Test frequency calculation."""
        words = ["apple", "banana", "apple", "orange", "banana", "banana"]
        
        frequency = trend_analyzer.calculate_frequency(words)
        
        # Verify frequencies
        assert frequency["banana"] == 3
        assert frequency["apple"] == 2
        assert frequency["orange"] == 1

    def test_calculate_term_frequency(self, trend_analyzer):
        """Test term frequency calculation."""
        doc = "apple banana apple orange banana banana"
        doc_words = doc.split()
        
        tf = trend_analyzer.calculate_term_frequency(doc_words)
        
        # Verify term frequencies
        assert tf["banana"] == 3/6  # 3 occurrences out of 6 words
        assert tf["apple"] == 2/6   # 2 occurrences out of 6 words
        assert tf["orange"] == 1/6  # 1 occurrence out of 6 words

    def test_calculate_idf(self, trend_analyzer):
        """Test inverse document frequency calculation."""
        docs = [
            "apple banana orange",
            "apple banana",
            "orange grape"
        ]
        
        docs_words = [doc.split() for doc in docs]
        
        idf = trend_analyzer.calculate_idf(docs_words)
        
        # Verify IDF values (using logarithm base 10)
        # apple appears in 2/3 docs, banana in 2/3, orange in 2/3, grape in 1/3
        import math
        assert idf["apple"] == math.log10(3/2)
        assert idf["banana"] == math.log10(3/2)
        assert idf["orange"] == math.log10(3/2)
        assert idf["grape"] == math.log10(3/1)

    def test_calculate_tfidf(self, trend_analyzer):
        """Test TF-IDF calculation."""
        docs = [
            "apple banana orange",
            "apple banana",
            "orange grape"
        ]
        
        docs_words = [doc.split() for doc in docs]
        
        tfidf_matrix = trend_analyzer.calculate_tfidf(docs_words)
        
        # Verify TF-IDF matrix
        assert isinstance(tfidf_matrix, list)
        assert len(tfidf_matrix) == 3  # One entry per document
        
        # Check matrix values
        for doc_tfidf in tfidf_matrix:
            assert isinstance(doc_tfidf, dict)
            
        # First document should have scores for apple, banana, orange
        assert "apple" in tfidf_matrix[0]
        assert "banana" in tfidf_matrix[0]
        assert "orange" in tfidf_matrix[0]
        
        # Third document should have scores for orange, grape
        assert "orange" in tfidf_matrix[2]
        assert "grape" in tfidf_matrix[2]

    def test_extract_trending_terms(self, trend_analyzer, sample_articles):
        """Test extraction of trending terms from articles."""
        # Get article titles for analysis
        titles = [article.title for article in sample_articles]
        
        # Extract trending terms
        trending_terms = trend_analyzer.extract_trending_terms(titles)
        
        # Verify trending terms
        assert isinstance(trending_terms, list)
        assert len(trending_terms) > 0
        
        # Each term should have a score
        for term_info in trending_terms:
            assert "term" in term_info
            assert "score" in term_info
            assert "frequency" in term_info

    def test_analyze_headline_trends(self, trend_analyzer, sample_articles, db_session):
        """Test analyzing headline trends and storing results."""
        # Analyze trends
        result = trend_analyzer.analyze_headline_trends(
            articles=sample_articles,
            time_period="day",
            store_results=True,
            session=db_session
        )
        
        # Verify result
        assert isinstance(result, dict)
        assert "trends" in result
        assert "analysis_id" in result
        
        # Verify trends were stored in database
        analysis = db_session.exec(
            select(TrendAnalysis).where(TrendAnalysis.id == result["analysis_id"])
        ).first()
        
        assert analysis is not None
        assert analysis.trend_type == TrendType.HEADLINE
        
        # Verify trend entities were created
        trend_entities = db_session.exec(
            select(TrendEntity).where(TrendEntity.analysis_id == analysis.id)
        ).all()
        
        assert len(trend_entities) > 0
        
        # Verify evidence items were created
        evidence_items = db_session.exec(
            select(TrendEvidenceItem).where(TrendEvidenceItem.analysis_id == analysis.id)
        ).all()
        
        assert len(evidence_items) > 0

    def test_calculate_trend_score(self, trend_analyzer):
        """Test calculation of trend scores."""
        # Set up test data with fake frequencies over time periods
        frequencies = {
            "term1": [1, 2, 3, 5, 8],  # Increasing trend
            "term2": [8, 5, 3, 2, 1],  # Decreasing trend
            "term3": [1, 1, 1, 1, 1],  # Stable (not trending)
            "term4": [0, 0, 0, 5, 10]  # Sudden spike
        }
        
        # Calculate trend scores
        scores = {}
        for term, freq in frequencies.items():
            scores[term] = trend_analyzer.calculate_trend_score(freq)
        
        # Verify trend scores reflect the expected patterns
        # Increasing trends should have higher scores than decreasing ones
        assert scores["term1"] > scores["term2"]
        
        # Sudden spikes should have high scores
        assert scores["term4"] > scores["term3"]
        
        # Stable frequencies should have low scores
        assert scores["term3"] == 0  # No change means no trend

    def test_generate_trend_summary(self, trend_analyzer, db_session):
        """Test generating a trend summary."""
        # Create a test trend analysis
        analysis = TrendAnalysis(
            trend_type=TrendType.HEADLINE,
            time_period="day",
            start_date=datetime.now(timezone.utc) - timedelta(days=7),
            end_date=datetime.now(timezone.utc),
            status=TrendStatus.COMPLETED,
            metadata={"source": "test"}
        )
        db_session.add(analysis)
        db_session.commit()
        db_session.refresh(analysis)
        
        # Create trend entities
        trend_entities = []
        for i, term in enumerate(["AI", "Climate Change", "Politics"]):
            entity = TrendEntity(
                analysis_id=analysis.id,
                term=term,
                score=0.8 - (i * 0.2),  # Decreasing scores
                frequency=10 - i,
                metadata={}
            )
            db_session.add(entity)
            db_session.commit()
            db_session.refresh(entity)
            trend_entities.append(entity)
            
            # Add evidence items
            for j in range(3):
                evidence = TrendEvidenceItem(
                    analysis_id=analysis.id,
                    trend_entity_id=entity.id,
                    evidence_type="article",
                    content=f"Evidence {j} for {term}",
                    metadata={"source": "test"}
                )
                db_session.add(evidence)
        db_session.commit()
        
        # Generate summary
        summary = trend_analyzer.generate_trend_summary(analysis.id, session=db_session)
        
        # Verify summary
        assert isinstance(summary, dict)
        assert "analysis" in summary
        assert "trends" in summary
        assert "evidence" in summary
        
        # Verify analysis details
        assert summary["analysis"]["id"] == analysis.id
        assert summary["analysis"]["trend_type"] == TrendType.HEADLINE.value
        
        # Verify trends are sorted by score
        trends = summary["trends"]
        assert len(trends) == 3
        assert trends[0]["term"] == "AI"  # Highest score
        
        # Verify evidence is grouped by term
        evidence = summary["evidence"]
        assert len(evidence) == 3
        assert "AI" in evidence
        assert len(evidence["AI"]) == 3  # 3 evidence items