"""Tests for injectable SentimentTracker pattern."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

# Import event loop fixture to handle fastapi-injectable async operations
from tests.fixtures.event_loop import event_loop_fixture
from tests.ci_skip_config import ci_skip_async, ci_skip_injectable

# Mock imports
patch('spacy.load', MagicMock(return_value=MagicMock())).start()
patch('textblob.TextBlob', MagicMock(return_value=MagicMock(
    sentiment=MagicMock(polarity=0.5, subjectivity=0.7)
))).start()

# Mock fastapi-injectable to prevent dependency resolution issues in tests
injectable_mock = MagicMock()
injectable_mock.side_effect = lambda **kwargs: lambda f: f
patch('fastapi_injectable.injectable', injectable_mock).start()


class TestInjectableSentimentTracker:
    """Test class for the injectable SentimentTracker pattern."""
    
    @pytest.fixture(autouse=True)
    def setup_event_loop(self, event_loop_fixture):
        """Ensure every test in this class has access to the event loop fixture."""
        return event_loop_fixture
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = MagicMock()
        return session
        
    @ci_skip_injectable
    def test_provider_function(self, mock_session, event_loop_fixture):
        """Test that provider functions create a properly configured SentimentTracker.

        This test is skipped in CI environments due to issues with fastapi-injectable's
        dependency resolution that causes event loop errors.
        """
        # Import here after patching
        with patch('local_newsifier.di.providers.get_session', return_value=mock_session):
            from local_newsifier.di.providers import get_sentiment_tracker_tool
            from local_newsifier.tools.sentiment_tracker import SentimentTracker

            # Mock the Depends function to avoid event loop issues
            with patch('fastapi.Depends', return_value=mock_session):
                # Get tracker from provider function - directly call without using Depends
                tracker = get_sentiment_tracker_tool(session=mock_session)

                # Verify tracker is properly configured
                assert isinstance(tracker, SentimentTracker)
                assert tracker.session_factory is not None
                assert tracker.session_factory() is mock_session
            
    def test_session_injection(self, mock_session):
        """Test that the session is properly injected and used."""
        # Import the class directly to test in isolation
        from local_newsifier.tools.sentiment_tracker import SentimentTracker

        # Create instance with session_factory - a simple test
        tracker = SentimentTracker(session_factory=lambda: mock_session)

        # Just verify that the session is correctly stored and retrievable
        assert tracker.session_factory is not None
        assert tracker.session_factory() is mock_session

        # Test the _get_session method directly
        retrieved_session = tracker._get_session()
        assert retrieved_session is mock_session, "Session factory should provide the mock session"
                
    def test_session_priority(self, mock_session):
        """Test that the session priority logic works correctly."""
        from local_newsifier.tools.sentiment_tracker import SentimentTracker
        
        # Create different sessions for testing priority
        session1 = MagicMock(name="session1")
        session2 = MagicMock(name="session2")
        factory_session = MagicMock(name="factory_session")
        
        # Create tracker with factory session
        tracker = SentimentTracker(session=session1, session_factory=lambda: factory_session)
        
        # Test case 1: Explicitly provided session has highest priority
        result1 = tracker._get_session(session=session2)
        assert result1 is session2, "Explicitly provided session should have highest priority"
        
        # Test case 2: Factory session has second priority
        result2 = tracker._get_session()
        assert result2 is factory_session, "Factory session should have second priority"
        
        # Test case 3: Instance session has lowest priority
        tracker_no_factory = SentimentTracker(session=session1)
        result3 = tracker_no_factory._get_session()
        assert result3 is session1, "Instance session should be used when no factory"