"""Tests for the OpinionVisualizerTool."""

import pytest
from unittest.mock import MagicMock
from sqlmodel import Session

from local_newsifier.tools.opinion_visualizer import OpinionVisualizerTool


class TestOpinionVisualizer:
    """Test class for OpinionVisualizerTool."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return MagicMock(spec=Session)

    @pytest.fixture
    def visualizer(self, mock_session):
        """Create an opinion visualizer instance."""
        return OpinionVisualizerTool(session=mock_session)

    def test_initialization(self):
        """Test that the class can be initialized properly with dependencies."""
        # Create a mock session
        mock_session = MagicMock(spec=Session)
        
        # Initialize the tool directly
        visualizer = OpinionVisualizerTool(session=mock_session)
        
        # Assert
        assert visualizer.session == mock_session
        assert isinstance(visualizer, OpinionVisualizerTool)