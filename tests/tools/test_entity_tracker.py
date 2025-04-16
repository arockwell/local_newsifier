"""Tests for the Entity Tracker tool."""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from local_newsifier.tools.entity_tracker import EntityTracker


@patch("spacy.load")
def test_entity_tracker_init(mock_spacy_load):
    """Test initializing the entity tracker."""
    mock_spacy_load.return_value = Mock()
    
    tracker = EntityTracker()
    
    # spacy.load is called twice: once for EntityTracker, once for ContextAnalyzer
    assert mock_spacy_load.call_count == 2
    assert mock_spacy_load.call_args_list[0][0][0] == "en_core_web_lg"
    
    assert tracker.nlp is not None
    assert tracker.entity_resolver is not None
    assert tracker.context_analyzer is not None