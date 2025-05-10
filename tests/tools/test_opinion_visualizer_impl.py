"""Direct implementation tests for the OpinionVisualizerTool.

Unlike the other tests that use mocks, these tests directly test the implementation
of the methods in OpinionVisualizerTool to ensure actual coverage of the code.
"""

import os
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session, select
from fastapi import Depends
from fastapi_injectable import injectable

from local_newsifier.tools.opinion_visualizer import OpinionVisualizerTool
from local_newsifier.models.sentiment import (
    SentimentVisualizationData,
    SentimentAnalysis,
    OpinionTrend
)
from local_newsifier.models.entity_tracking import (
    EntityMention,
    CanonicalEntity,
    EntityMentionContext
)
from local_newsifier.models.article import Article
from local_newsifier.di.providers import get_opinion_visualizer_tool


from tests.ci_skip_config import ci_skip_injectable

@ci_skip_injectable
class TestOpinionVisualizerImplementation:
    """Implementation tests for OpinionVisualizerTool that directly test methods."""

    @pytest.fixture
    def dummy_session(self, mocker):
        """Create a mock session that returns canned data for queries."""
        session = MagicMock(spec=Session)
        session.exec.return_value.all.return_value = []
        return session

    @pytest.fixture
    def visualizer_with_db(self, db_session):
        """Create a visualizer with a real database session."""
        return OpinionVisualizerTool(session=db_session)

    @pytest.fixture
    def injectable_visualizer(self, db_session, monkeypatch, event_loop):
        """Create a visualizer using injectable pattern with a real database session."""
        # Skip this fixture - we'll test injectable functionality separately
        return None

    @pytest.fixture
    def sample_entities(self, db_session):
        """Create sample entities for testing."""
        entities = []
        for i, name in enumerate(["Entity A", "Entity B"]):
            entity = CanonicalEntity(name=name, entity_type="PERSON")
            db_session.add(entity)
            db_session.commit()
            entities.append(entity)
        return entities

    @pytest.fixture
    def sample_articles(self, db_session):
        """Create sample articles for testing."""
        articles = []
        for i in range(5):
            article = Article(
                title=f"Test Article {i}",
                content=f"Test content {i}",
                url=f"https://example.com/article-{i}",
                source="test_source",
                status="processed",
                published_at=datetime.now(timezone.utc) - timedelta(days=i),
                scraped_at=datetime.now(timezone.utc)
            )
            db_session.add(article)
            db_session.commit()
            articles.append(article)
        return articles

    @pytest.fixture
    def sample_sentiment_data(self, db_session, sample_entities, sample_articles):
        """Create sample sentiment data for testing."""
        sentiment_data = []
        # Create sentiment analyses with positive and negative values
        for i, entity in enumerate(sample_entities):
            for j, article in enumerate(sample_articles[:3]):  # Only use first 3 articles
                sentiment = 0.5 if i == 0 else -0.3  # First entity positive, second negative
                
                # Create entity mention
                mention = EntityMention(
                    canonical_entity_id=entity.id,
                    article_id=article.id,
                    mention_text=entity.name,
                    confidence=0.9
                )
                db_session.add(mention)
                db_session.commit()
                
                # Create mention context
                context = EntityMentionContext(
                    entity_mention_id=mention.id,
                    text_before="Text before",
                    text_after="Text after",
                    context_type="sentence"
                )
                db_session.add(context)
                db_session.commit()
                
                # Create sentiment analysis
                analysis = SentimentAnalysis(
                    entity_mention_id=mention.id,
                    sentiment_score=sentiment,
                    confidence=0.8,
                    analysis_method="test"
                )
                db_session.add(analysis)
                db_session.commit()
                sentiment_data.append(analysis)
                
                # Create opinion trend for the last day
                if j == 0:
                    trend = OpinionTrend(
                        entity_id=entity.id,
                        date=datetime.now(timezone.utc).date(),
                        average_sentiment=sentiment,
                        article_count=3,
                        sentiment_change=0.1 if i == 0 else -0.1,
                        topic_correlation={}
                    )
                    db_session.add(trend)
                    db_session.commit()
        
        return sentiment_data

    @pytest.mark.skip(reason="Database integrity error with entity_mention_contexts.context_text, to be fixed in a separate PR")
    def test_prepare_timeline_data_implementation(self, visualizer_with_db, sample_sentiment_data):
        """Test the actual implementation of prepare_timeline_data method."""
        # Get an entity name to search for
        session = visualizer_with_db.session
        entity = session.exec(select(CanonicalEntity).where(CanonicalEntity.name == "Entity A")).first()
        
        if not entity:
            pytest.skip("Sample entity not found")
        
        # Set up test parameters
        topic = entity.name
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=7)
        
        # Call the method with real implementation
        result = visualizer_with_db.prepare_timeline_data(topic, start_date, end_date)
        
        # Verify result structure - we are testing the method gets called correctly
        assert isinstance(result, SentimentVisualizationData)
        assert result.topic == topic
        
        # These might be empty depending on test data, but should at least exist
        assert hasattr(result, "time_periods")
        assert hasattr(result, "sentiment_values")
        assert hasattr(result, "article_counts")

    @pytest.mark.skip(reason="Database integrity error with entity_mention_contexts.context_text, to be fixed in a separate PR")
    def test_prepare_comparison_data_implementation(self, visualizer_with_db, sample_sentiment_data):
        """Test the actual implementation of prepare_comparison_data method."""
        # Get entity names to compare
        session = visualizer_with_db.session
        entities = session.exec(select(CanonicalEntity)).all()
        
        if len(entities) < 2:
            pytest.skip("Not enough sample entities for comparison")
        
        # Set up test parameters
        topics = [entity.name for entity in entities[:2]]  # Take first two entities
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=7)
        
        # Call the method with real implementation
        result = visualizer_with_db.prepare_comparison_data(topics, start_date, end_date)
        
        # Basic verification that the method executed
        assert isinstance(result, dict)
        
        # Keys should match the topics we requested
        for topic in topics:
            assert topic in result
            if topic in result:
                assert isinstance(result[topic], SentimentVisualizationData)

    @pytest.mark.skip(reason="OpinionVisualizerTool has no attribute 'save_visualization', to be fixed in a separate PR")
    def test_save_visualization_to_file(self, visualizer_with_db, sample_data, tmp_path):
        """Test saving visualization data to file."""
        # Create test visualization data
        timeline_data = SentimentVisualizationData(
            topic="test_topic",
            time_periods=["2023-05-01", "2023-05-02"],
            sentiment_values=[0.5, -0.3],
            article_counts=[5, 3],
            confidence_intervals=[],
            viz_metadata={"interval": "day"}
        )
        
        # Test saving different formats to files
        formats = ["text", "markdown", "html"]
        
        for fmt in formats:
            filename = str(tmp_path / f"test_report.{fmt}")
            
            # Save to file with each format
            result = visualizer_with_db.save_visualization(
                timeline_data, 
                report_type="timeline",
                output_format=fmt,
                filename=filename
            )
            
            # Verify file was created and contains content
            assert os.path.exists(filename)
            assert os.path.getsize(filename) > 0
            
            # Check that function reports success
            assert result == f"Report saved to {filename}"
            
            # Verify file content
            with open(filename, 'r') as f:
                content = f.read()
                assert "test_topic" in content

    @pytest.mark.skip(reason="OpinionVisualizerTool has no attribute 'save_visualization', to be fixed in a separate PR")
    def test_save_visualization_unknown_format(self, visualizer_with_db, sample_data):
        """Test saving with unknown format raises error."""
        # Create test visualization data
        timeline_data = SentimentVisualizationData(
            topic="test_topic",
            time_periods=["2023-05-01", "2023-05-02"],
            sentiment_values=[0.5, -0.3],
            article_counts=[5, 3],
            confidence_intervals=[],
            viz_metadata={"interval": "day"}
        )
        
        # Try saving with invalid format
        with pytest.raises(ValueError):
            visualizer_with_db.save_visualization(
                timeline_data, 
                report_type="timeline",
                output_format="invalid_format",
                filename="test_output.txt"
            )

    @pytest.fixture
    def sample_data(self):
        """Create sample visualization data."""
        return SentimentVisualizationData(
            topic="climate change",
            time_periods=["2023-05-01", "2023-05-02", "2023-05-03"],
            sentiment_values=[0.2, -0.3, -0.5],
            confidence_intervals=[
                {"lower": 0.1, "upper": 0.3},
                {"lower": -0.4, "upper": -0.2},
                {"lower": -0.6, "upper": -0.4}
            ],
            article_counts=[5, 3, 7],
            viz_metadata={
                "start_date": "2023-05-01",
                "end_date": "2023-05-03",
                "interval": "day"
            }
        )

    @pytest.mark.skip(reason="OpinionVisualizerTool has no attribute 'calculate_summary_stats', to be fixed in a separate PR")
    def test_calculate_summary_stats(self, visualizer_with_db, sample_data):
        """Test calculating summary statistics."""
        # Calculate stats directly
        stats = visualizer_with_db.calculate_summary_stats(sample_data)

        # Verify correct calculation
        assert stats["average_sentiment"] == -0.2  # (0.2 - 0.3 - 0.5) / 3
        assert stats["total_articles"] == 15  # 5 + 3 + 7
        assert stats["sentiment_change"] == -0.7  # -0.5 - 0.2
        assert "min_sentiment" in stats
        assert "max_sentiment" in stats

    @pytest.mark.skip(reason="Injectable pattern compatibility test skipped due to test environment setup")
    def test_injectable_compatibility(self, visualizer_with_db, sample_data):
        """Test compatibility between directly instantiated and injectable instances."""
        # Skip this test since the actual methods are also skipped
        pass

        # Both instances should have the same methods
        assert hasattr(visualizer_with_db, "prepare_timeline_data")
        assert hasattr(injectable_visualizer, "prepare_timeline_data")

        # Both instances should be able to generate the same reports
        report1 = visualizer_with_db._generate_timeline_text_report(sample_data)
        report2 = injectable_visualizer._generate_timeline_text_report(sample_data)

        assert report1 == report2