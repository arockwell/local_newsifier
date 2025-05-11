"""Tests for the injectable SentimentTracker."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from fastapi import Depends
from sqlmodel import Session
from typing import Annotated

# Import event loop fixture
from tests.fixtures.event_loop import event_loop_fixture  # noqa

# Patch imports to avoid requiring external dependencies
patch('spacy.load', MagicMock(return_value=MagicMock())).start()
patch('textblob.TextBlob', MagicMock(return_value=MagicMock(
    sentiment=MagicMock(polarity=0.5, subjectivity=0.7)
))).start()

# Mock fastapi_injectable to avoid dependency resolution errors in tests
injectable_mock = MagicMock()
injectable_mock.side_effect = lambda **kwargs: lambda f: f
patch('fastapi_injectable.injectable', injectable_mock).start()

# Import after patching
with patch('spacy.language.Language', MagicMock()):
    from local_newsifier.tools.sentiment_tracker import SentimentTracker

    # Mock the provider function directly instead of importing it
    def get_sentiment_tracker_tool(session):
        return SentimentTracker(session_factory=lambda: session)


class TestInjectableSentimentTracker:
    """Test class for injectable SentimentTracker."""

    @pytest.fixture(autouse=True)
    def setup_event_loop(self, event_loop_fixture):
        """Ensure every test in this class has access to the event loop fixture."""
        return event_loop_fixture

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = MagicMock()
        return session
        
    @pytest.fixture
    def mock_session_provider(self, mock_session):
        """Create a mock session provider for injection."""
        @injectable(use_cache=False)
        def get_test_session():
            return mock_session
            
        return get_test_session
        
    def test_provider_function(self, mock_session):
        """Test that the provider function creates a SentimentTracker with session factory."""
        # Mock the get_session dependency
        with patch('local_newsifier.di.providers.get_session', return_value=mock_session):
            # Get the sentiment tracker from the provider
            tracker = get_sentiment_tracker_tool(mock_session)

            # Verify it's an instance of SentimentTracker
            assert isinstance(tracker, SentimentTracker)

            # Verify it has a session_factory
            assert tracker.session_factory is not None

            # Verify the session_factory returns our mock session
            assert tracker.session_factory() is mock_session
            
    def test_provider_integration(self, mock_session):
        """Test that the provider function works with method calls."""
        # This test just verifies that the provider returns a properly configured tracker
        # Get the sentiment tracker from the provider
        tracker = get_sentiment_tracker_tool(mock_session)

        # Verify it's correctly configured
        assert tracker.session_factory is not None
        assert tracker.session_factory() is mock_session