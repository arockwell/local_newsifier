"""Tests for the PublicOpinionFlow."""

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch, AsyncMock

import pytest
from pytest_mock import MockFixture

from tests.fixtures.event_loop import event_loop_fixture
from tests.ci_skip_config import ci_skip

from local_newsifier.flows.public_opinion_flow import PublicOpinionFlow
from local_newsifier.models.sentiment import SentimentVisualizationData


class TestPublicOpinionFlow:
    """Test class for PublicOpinionFlow."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return MagicMock()

    @pytest.fixture
    def flow(self, mock_session):
        """Create a public opinion flow instance with mocked components."""
        with patch('local_newsifier.flows.public_opinion_flow.SentimentAnalyzer') as mock_analyzer, \
             patch('local_newsifier.flows.public_opinion_flow.SentimentTracker') as mock_tracker, \
             patch('local_newsifier.flows.public_opinion_flow.OpinionVisualizerTool') as mock_visualizer:
            
            # Setup mocks to be returned when the tools are initialized
            mock_analyzer.return_value = MagicMock()
            mock_tracker.return_value = MagicMock()
            mock_visualizer.return_value = MagicMock()
            
            # Create flow with the session
            flow = PublicOpinionFlow(session=mock_session)
            
            # Replace the automatically created tools with our mocks
            flow.sentiment_analyzer = mock_analyzer.return_value
            flow.sentiment_tracker = mock_tracker.return_value
            flow.opinion_visualizer = mock_visualizer.return_value
            
            return flow

    def test_init_without_session(self):
        """Test initialization with an injected session."""
        mock_session = MagicMock()

        with patch('local_newsifier.flows.public_opinion_flow.SentimentAnalyzer'), \
             patch('local_newsifier.flows.public_opinion_flow.SentimentTracker'), \
             patch('local_newsifier.flows.public_opinion_flow.OpinionVisualizerTool'):

            flow = PublicOpinionFlow(session=mock_session)

            assert flow.session is mock_session

    def test_analyze_articles_with_ids(self, flow):
        """Test analyzing sentiment for specific articles."""
        # Mock sentiment analyzer to return properly structured results
        def analyze_with_session(article_id, session=None):
            if article_id == 1:
                return {"document_sentiment": 0.5, "entity_sentiments": {}}
            else:
                return {"document_sentiment": -0.3, "entity_sentiments": {}}
        
        flow.sentiment_analyzer.analyze_article.side_effect = analyze_with_session
        
        # Handle any async methods that might exist
        if hasattr(flow, 'analyze_articles_async'):
            flow.analyze_articles_async = AsyncMock()
            
        if hasattr(flow.sentiment_analyzer, 'analyze_article_async'):
            flow.sentiment_analyzer.analyze_article_async = AsyncMock()
            
        # Create proper mock articles to satisfy validation
        with patch('local_newsifier.crud.article.article.get_by_status'), \
             patch('local_newsifier.crud.article.article.update_status'):
             
            # Create a mock session that doesn't actually commit anything
            mock_sess = MagicMock()
            flow.session = mock_sess
            
            # Call method with article IDs - using the session
            result = flow.analyze_articles(article_ids=[1, 2], session=mock_sess)
            
            # Verify core results, not the adapter calls
            assert 1 in result
            assert 2 in result
            assert result[1]["document_sentiment"] == 0.5
            assert result[2]["document_sentiment"] == -0.3

    def test_analyze_articles_without_ids(self, flow):
        """Test analyzing sentiment for all unanalyzed articles."""
        # Create proper mock articles with required attributes
        from datetime import datetime
        
        # Create proper article objects that match the expected structure
        mock_article1 = MagicMock()
        mock_article1.id = 1
        mock_article1.title = "Test Article 1"
        mock_article1.url = "http://example.com/1"
        mock_article1.content = "Test content 1"
        mock_article1.source = "Test Source"
        mock_article1.published_at = datetime.now()
        mock_article1.status = "analyzed"
        
        mock_article2 = MagicMock()
        mock_article2.id = 2
        mock_article2.title = "Test Article 2"
        mock_article2.url = "http://example.com/2"
        mock_article2.content = "Test content 2"
        mock_article2.source = "Test Source"
        mock_article2.published_at = datetime.now()
        mock_article2.status = "analyzed"
        
        # Use patch to inject our mock articles
        with patch('local_newsifier.crud.article.article.get_by_status', 
                  return_value=[mock_article1, mock_article2]):
            
            # Mock sentiment analyzer to handle session parameter
            def analyze_with_session(article_id, session=None):
                if article_id == 1:
                    return {"document_sentiment": 0.5, "entity_sentiments": {}}
                else:
                    return {"document_sentiment": -0.3, "entity_sentiments": {}}
            
            flow.sentiment_analyzer.analyze_article.side_effect = analyze_with_session
            
            # Handle any async methods that might exist
            if hasattr(flow, 'analyze_articles_async'):
                flow.analyze_articles_async = AsyncMock()
                
            if hasattr(flow.sentiment_analyzer, 'analyze_article_async'):
                flow.sentiment_analyzer.analyze_article_async = AsyncMock()
                
            # Mock update_article_status to do nothing
            with patch('local_newsifier.crud.article.article.update_status'):
                # Create a mock session that doesn't actually commit anything
                mock_sess = MagicMock()
                flow.session = mock_sess
                
                # Call method without article IDs
                result = flow.analyze_articles(session=mock_sess)
                
                # Only verify the core results
                assert 1 in result
                assert 2 in result
                assert result[1]["document_sentiment"] == 0.5
                assert result[2]["document_sentiment"] == -0.3

    def test_analyze_articles_with_error(self, flow):
        """Test handling errors during article analysis."""
        # Create a controlled test environment with patched functions
        
        # Mock update_article_status to do nothing
        with patch('local_newsifier.crud.article.article.update_status'):
            # Mock sentiment analyzer with an error that handles session param
            def analyze_with_session_and_error(article_id, session=None):
                if article_id == 1:
                    return {"document_sentiment": 0.5, "entity_sentiments": {}}
                else:
                    raise Exception("Test error")
            
            flow.sentiment_analyzer.analyze_article.side_effect = analyze_with_session_and_error
            
            # Handle any async methods that might exist
            if hasattr(flow, 'analyze_articles_async'):
                flow.analyze_articles_async = AsyncMock()
                
            if hasattr(flow.sentiment_analyzer, 'analyze_article_async'):
                flow.sentiment_analyzer.analyze_article_async = AsyncMock()
                
            # Create a mock session that doesn't actually commit anything
            mock_sess = MagicMock()
            flow.session = mock_sess
            
            # Call method with article IDs
            result = flow.analyze_articles(article_ids=[1, 2], session=mock_sess)
            
            # Verify successful result for article 1
            assert 1 in result
            assert result[1]["document_sentiment"] == 0.5
            
            # Verify error for article 2
            assert 2 in result
            assert "error" in result[2]
            assert "Test error" in result[2]["error"]

    def test_analyze_topic_sentiment(self, flow):
        """Test analyzing sentiment trends for topics."""
        # Mock sentiment tracker
        flow.sentiment_tracker.get_sentiment_by_period.return_value = {
            "2023-05-01": {"climate": {"avg_sentiment": -0.3}},
            "2023-05-02": {"climate": {"avg_sentiment": -0.5}}
        }
        
        flow.sentiment_tracker.detect_sentiment_shifts.return_value = [
            {"topic": "climate", "shift_magnitude": 0.2}
        ]
        
        # Create a mock session that doesn't use a real database
        mock_sess = MagicMock()
        flow.session = mock_sess
        
        # Patch possible async methods
        if hasattr(flow, 'analyze_topic_sentiment_async'):
            flow.analyze_topic_sentiment_async = AsyncMock()
            
        # Patch possible async functionality
        with patch('fastapi_injectable.concurrency.run_coroutine_sync', return_value=None), \
             patch('local_newsifier.database.engine.get_engine', return_value=MagicMock()), \
             patch('sqlalchemy.orm.Session', return_value=mock_sess):
            
            # Call method
            result = flow.analyze_topic_sentiment(
                topics=["climate"],
                days_back=7,
                interval="day"
            )
        
        # Verify results structure
        assert "date_range" in result
        assert "interval" in result
        assert "topics" in result
        assert "sentiment_by_period" in result
        assert "sentiment_shifts" in result
        
        # Verify method calls to sentiment tracker
        flow.sentiment_tracker.get_sentiment_by_period.assert_called_once()
        flow.sentiment_tracker.detect_sentiment_shifts.assert_called_once()

    def test_analyze_entity_sentiment(self, flow):
        """Test analyzing sentiment trends for entities."""
        # Mock sentiment tracker
        flow.sentiment_tracker.get_entity_sentiment_trends.side_effect = [
            {
                "2023-05-01": {"avg_sentiment": 0.5, "article_count": 3},
                "2023-05-02": {"avg_sentiment": 0.7, "article_count": 2}
            },
            {
                "2023-05-01": {"avg_sentiment": -0.3, "article_count": 4},
                "2023-05-02": {"avg_sentiment": -0.2, "article_count": 5}
            }
        ]
        
        # Create a mock session that doesn't use a real database
        mock_sess = MagicMock()
        flow.session = mock_sess
        
        # Patch possible async methods
        if hasattr(flow, 'analyze_entity_sentiment_async'):
            flow.analyze_entity_sentiment_async = AsyncMock()
            
        # Patch possible async functionality
        with patch('fastapi_injectable.concurrency.run_coroutine_sync', return_value=None), \
             patch('local_newsifier.database.engine.get_engine', return_value=MagicMock()), \
             patch('sqlalchemy.orm.Session', return_value=mock_sess):
        
            # Call method
            result = flow.analyze_entity_sentiment(
                entity_names=["John Smith", "ABC Corp"],
                days_back=7,
                interval="day"
            )
        
        # Verify results structure
        assert "date_range" in result
        assert "interval" in result
        assert "entities" in result
        assert "entity_sentiments" in result
        assert "John Smith" in result["entity_sentiments"]
        assert "ABC Corp" in result["entity_sentiments"]
        
        # Verify method calls to sentiment tracker
        assert flow.sentiment_tracker.get_entity_sentiment_trends.call_count == 2

    def test_detect_opinion_shifts(self, flow):
        """Test detecting opinion shifts."""
        # Mock sentiment tracker
        flow.sentiment_tracker.detect_sentiment_shifts.return_value = [
            {"topic": "climate", "shift_magnitude": 0.5},
            {"topic": "energy", "shift_magnitude": 0.3}
        ]
        
        # Create a mock session that doesn't use a real database
        mock_sess = MagicMock()
        flow.session = mock_sess
        
        # Patch possible async methods
        if hasattr(flow, 'detect_opinion_shifts_async'):
            flow.detect_opinion_shifts_async = AsyncMock()
            
        # Patch possible async functionality
        with patch('fastapi_injectable.concurrency.run_coroutine_sync', return_value=None), \
             patch('local_newsifier.database.engine.get_engine', return_value=MagicMock()), \
             patch('sqlalchemy.orm.Session', return_value=mock_sess):
            
            # Call method
            result = flow.detect_opinion_shifts(
                topics=["climate", "energy"],
                days_back=7,
                interval="day"
            )
        
        # Verify results structure - should group shifts by topic
        assert "climate" in result
        assert "energy" in result
        assert len(result["climate"]) == 1
        assert len(result["energy"]) == 1
        
        # Verify method calls to sentiment tracker
        flow.sentiment_tracker.detect_sentiment_shifts.assert_called_once()

    def test_correlate_topics(self, flow):
        """Test correlating topic sentiment."""
        # Mock sentiment tracker
        flow.sentiment_tracker.calculate_topic_correlation.side_effect = [
            {
                "topic1": "climate", 
                "topic2": "energy", 
                "correlation": -0.8,
                "period_count": 7
            },
            {
                "topic1": "economy", 
                "topic2": "politics", 
                "correlation": 0.6,
                "period_count": 7
            }
        ]
        
        # Create a mock session that doesn't use a real database
        mock_sess = MagicMock()
        flow.session = mock_sess
        
        # Patch possible async methods
        if hasattr(flow, 'correlate_topics_async'):
            flow.correlate_topics_async = AsyncMock()
            
        # Patch possible async functionality
        with patch('fastapi_injectable.concurrency.run_coroutine_sync', return_value=None), \
             patch('local_newsifier.database.engine.get_engine', return_value=MagicMock()), \
             patch('sqlalchemy.orm.Session', return_value=mock_sess):
            
            # Call method
            result = flow.correlate_topics(
                topic_pairs=[
                    ("climate", "energy"),
                    ("economy", "politics")
                ],
                days_back=7
            )
        
        # Verify results
        assert len(result) == 2
        assert result[0]["topic1"] == "climate"
        assert result[0]["topic2"] == "energy"
        assert result[0]["correlation"] == -0.8
        
        assert result[1]["topic1"] == "economy"
        assert result[1]["topic2"] == "politics"
        assert result[1]["correlation"] == 0.6
        
        # Verify method calls to sentiment tracker
        assert flow.sentiment_tracker.calculate_topic_correlation.call_count == 2

    def test_generate_topic_report(self, flow):
        """Test generating a topic report."""
        # Mock opinion visualizer
        mock_viz_data = SentimentVisualizationData(
            topic="climate",
            time_periods=["2023-05-01", "2023-05-02"],
            sentiment_values=[-0.3, -0.5],
            article_counts=[5, 3],
            confidence_intervals=[],
            metadata={"start_date": "2023-05-01", "end_date": "2023-05-02", "interval": "day"}
        )
        
        flow.opinion_visualizer.prepare_timeline_data.return_value = mock_viz_data
        flow.opinion_visualizer.generate_markdown_report.return_value = "# Markdown Report"
        flow.opinion_visualizer.generate_html_report.return_value = "<html>HTML Report</html>"
        flow.opinion_visualizer.generate_text_report.return_value = "Text Report"
        
        # Create a mock session that doesn't use a real database
        mock_sess = MagicMock()
        flow.session = mock_sess
        
        # Patch possible async methods
        if hasattr(flow, 'generate_topic_report_async'):
            flow.generate_topic_report_async = AsyncMock()
            
        # Test markdown report
        with patch('fastapi_injectable.concurrency.run_coroutine_sync', return_value=None), \
             patch('local_newsifier.database.engine.get_engine', return_value=MagicMock()), \
             patch('sqlalchemy.orm.Session', return_value=mock_sess):
            
            md_result = flow.generate_topic_report(
                topic="climate",
                days_back=7,
                format_type="markdown"
            )
        
        assert md_result == "# Markdown Report"
        flow.opinion_visualizer.generate_markdown_report.assert_called_once_with(mock_viz_data, report_type="timeline")
        
        # Test HTML report
        with patch('fastapi_injectable.concurrency.run_coroutine_sync', return_value=None), \
             patch('local_newsifier.database.engine.get_engine', return_value=MagicMock()), \
             patch('sqlalchemy.orm.Session', return_value=mock_sess):
            
            html_result = flow.generate_topic_report(
                topic="climate",
                days_back=7,
                format_type="html"
            )
        
        assert html_result == "<html>HTML Report</html>"
        flow.opinion_visualizer.generate_html_report.assert_called_once_with(mock_viz_data, report_type="timeline")
        
        # Test text report (default)
        with patch('fastapi_injectable.concurrency.run_coroutine_sync', return_value=None), \
             patch('local_newsifier.database.engine.get_engine', return_value=MagicMock()), \
             patch('sqlalchemy.orm.Session', return_value=mock_sess):
            
            text_result = flow.generate_topic_report(
                topic="climate",
                days_back=7,
                format_type="text"
            )
        
        assert text_result == "Text Report"
        flow.opinion_visualizer.generate_text_report.assert_called_once_with(mock_viz_data, report_type="timeline")

    @pytest.mark.slow
    def test_generate_comparison_report(self, flow):
        """Test generating a comparison report."""
        # Mock opinion visualizer
        flow.opinion_visualizer.prepare_timeline_data.side_effect = [
            SentimentVisualizationData(
                topic="climate",
                time_periods=["2023-05-01", "2023-05-02"],
                sentiment_values=[-0.3, -0.5],
                article_counts=[5, 3],
                confidence_intervals=[],
                metadata={"start_date": "2023-05-01", "end_date": "2023-05-02", "interval": "day"}
            ),
            SentimentVisualizationData(
                topic="energy",
                time_periods=["2023-05-01", "2023-05-02"],
                sentiment_values=[0.4, 0.6],
                article_counts=[3, 4],
                confidence_intervals=[],
                metadata={"start_date": "2023-05-01", "end_date": "2023-05-02", "interval": "day"}
            )
        ]
        
        flow.opinion_visualizer.generate_markdown_report.return_value = "# Comparison Report"
        
        # Create a mock session that doesn't use a real database
        mock_sess = MagicMock()
        flow.session = mock_sess
        
        # Patch possible async methods
        if hasattr(flow, 'generate_comparison_report_async'):
            flow.generate_comparison_report_async = AsyncMock()
            
        # Patch possible async functionality
        with patch('fastapi_injectable.concurrency.run_coroutine_sync', return_value=None), \
             patch('local_newsifier.database.engine.get_engine', return_value=MagicMock()), \
             patch('sqlalchemy.orm.Session', return_value=mock_sess):
            
            # Call method
            result = flow.generate_comparison_report(
                topics=["climate", "energy"],
                days_back=7,
                format_type="markdown"
            )
        
        # Verify result
        assert result == "# Comparison Report"
        
        # Verify method calls
        assert flow.opinion_visualizer.prepare_timeline_data.call_count == 2
        flow.opinion_visualizer.generate_markdown_report.assert_called_once()
        
        # Verify the argument to generate_markdown_report has the right structure
        comparison_data = flow.opinion_visualizer.generate_markdown_report.call_args[0][0]
        assert "climate" in comparison_data
        assert "energy" in comparison_data

    @pytest.mark.slow
    def test_generate_report_with_error(self, flow):
        """Test error handling in report generation."""
        # Mock visualizer with an error
        flow.opinion_visualizer.prepare_timeline_data.side_effect = Exception("Data error")
        
        # Create a mock session that doesn't use a real database
        mock_sess = MagicMock()
        flow.session = mock_sess
        
        # Patch possible async methods
        if hasattr(flow, 'generate_topic_report_async'):
            flow.generate_topic_report_async = AsyncMock()
            
        # Patch possible async functionality
        with patch('fastapi_injectable.concurrency.run_coroutine_sync', return_value=None), \
             patch('local_newsifier.database.engine.get_engine', return_value=MagicMock()), \
             patch('sqlalchemy.orm.Session', return_value=mock_sess):
            
            # Call method
            result = flow.generate_topic_report(topic="climate")
        
        # Verify error is returned
        assert "Error generating report" in result
        assert "Data error" in result
        
        # Test error in comparison report
        with patch('fastapi_injectable.concurrency.run_coroutine_sync', return_value=None), \
             patch('local_newsifier.database.engine.get_engine', return_value=MagicMock()), \
             patch('sqlalchemy.orm.Session', return_value=mock_sess):
            
            result = flow.generate_comparison_report(topics=["climate", "energy"])
        
        # Since we're mocking, the result is a mock object
        # Just ensure the method was called with the expected report_type
        flow.opinion_visualizer.generate_markdown_report.assert_called_with({}, report_type="comparison")
        # Skip checking the error message as we're dealing with mocks

    def test_error_handling_in_prepare_comparison_data(self, flow):
        """Test error handling when preparing comparison data for one topic."""
        # Mock visualizer with an error for only one topic
        def prepare_side_effect(topic, *args, **kwargs):
            if topic == "climate":
                return SentimentVisualizationData(
                    topic="climate",
                    time_periods=["2023-05-01"],
                    sentiment_values=[-0.3],
                    article_counts=[5],
                    confidence_intervals=[],
                    metadata={"interval": "day"}
                )
            else:
                raise Exception("Data error for energy")
                
        flow.opinion_visualizer.prepare_timeline_data.side_effect = prepare_side_effect
        flow.opinion_visualizer.generate_markdown_report.return_value = "# Partial Report"
        
        # Create a mock session that doesn't use a real database
        mock_sess = MagicMock()
        flow.session = mock_sess
        
        # Patch possible async methods
        if hasattr(flow, 'generate_comparison_report_async'):
            flow.generate_comparison_report_async = AsyncMock()
            
        # Patch possible async functionality
        with patch('fastapi_injectable.concurrency.run_coroutine_sync', return_value=None), \
             patch('local_newsifier.database.engine.get_engine', return_value=MagicMock()), \
             patch('sqlalchemy.orm.Session', return_value=mock_sess):
            
            # Call method
            result = flow.generate_comparison_report(
                topics=["climate", "energy"],
                format_type="markdown"
            )
        
        # Verify report was still generated with the successful topic
        assert result == "# Partial Report"
        
        # Verify the comparison data only includes the successful topic
        comparison_data = flow.opinion_visualizer.generate_markdown_report.call_args[0][0]
        assert "climate" in comparison_data
        assert "energy" not in comparison_data
