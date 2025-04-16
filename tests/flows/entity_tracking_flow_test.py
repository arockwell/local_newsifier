"""Tests for the Entity Tracking flow."""

from unittest.mock import Mock, patch

import pytest

from local_newsifier.flows.entity_tracking_flow import EntityTrackingFlow
from local_newsifier.tools.entity_tracker import EntityTracker


@patch("local_newsifier.flows.entity_tracking_flow.EntityTracker")
def test_entity_tracking_flow_init(mock_entity_tracker_class):
    """Test initializing the entity tracking flow."""
    mock_entity_tracker_class.return_value = Mock()
    
    flow = EntityTrackingFlow()
    
    mock_entity_tracker_class.assert_called_once()
    assert flow.entity_tracker is not None