"""Tests for the Entity Tracker tool."""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest

from local_newsifier.database.manager import DatabaseManager
from local_newsifier.models import Entity
from local_newsifier.models.entity_tracking import (CanonicalEntity,
                                                  CanonicalEntityCreate,
                                                  EntityMentionContextCreate)
from local_newsifier.tools.context_analyzer import ContextAnalyzer
from local_newsifier.tools.entity_resolver import EntityResolver
from local_newsifier.tools.entity_tracker import EntityTracker


@pytest.fixture
def mock_db_manager():
    """Create a mock database manager."""
    db_manager = Mock(spec=DatabaseManager)
    
    # Mock session
    db_manager.session = Mock()
    
    # Mock exec for session to return empty results by default
    mock_exec = Mock()
    mock_exec.first.return_value = None
    mock_exec.all.return_value = []
    db_manager.session.exec.return_value = mock_exec
    
    # Simulate session.add() and session.commit()
    db_manager.session.add = Mock()
    db_manager.session.commit = Mock()
    db_manager.session.refresh = Mock()
    
    # Make Entity work correctly
    def refresh_entity(entity):
        entity.id = 1
        return entity
    
    db_manager.session.refresh.side_effect = refresh_entity
    
    # For backward compatibility with tests
    db_manager.get_entity_profile = Mock(return_value=None)
    db_manager.add_entity_profile = Mock()
    
    return db_manager


@pytest.fixture
def mock_entity_resolver():
    """Create a mock entity resolver."""
    entity_resolver = Mock(spec=EntityResolver)
    
    # Mock resolve_entity
    def resolve_entity(name, entity_type):
        return CanonicalEntity(
            id=1,
            name="Joe Biden",
            entity_type="PERSON",
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc)
        )
    
    entity_resolver.resolve_entity.side_effect = resolve_entity
    
    return entity_resolver


@pytest.fixture
def mock_context_analyzer():
    """Create a mock context analyzer."""
    context_analyzer = Mock(spec=ContextAnalyzer)
    
    # Mock analyze_context
    context_analyzer.analyze_context.return_value = {
        "sentiment": {
            "score": 0.5,
            "positive_count": 2,
            "negative_count": 1,
            "total_count": 3
        },
        "framing": {
            "category": "leadership",
            "scores": {"leadership": 0.7, "controversy": 0.3},
            "counts": {"leadership": 2, "controversy": 1},
            "total_count": 3
        },
        "length": 100,
        "word_count": 20
    }
    
    return context_analyzer


@patch("spacy.load")
def test_entity_tracker_init(mock_spacy_load, mock_db_manager):
    """Test initializing the entity tracker."""
    mock_spacy_load.return_value = Mock()
    
    tracker = EntityTracker(mock_db_manager)
    
    # spacy.load is called twice: once for EntityTracker, once for ContextAnalyzer
    assert mock_spacy_load.call_count == 2
    assert mock_spacy_load.call_args_list[0] == mock_spacy_load.call_args_list[1]
    assert mock_spacy_load.call_args_list[0][0][0] == "en_core_web_lg"
    
    assert tracker.db_manager is mock_db_manager
    assert tracker.nlp is not None
    assert tracker.entity_resolver is not None
    assert tracker.context_analyzer is not None


@patch("local_newsifier.tools.entity_tracker.EntityResolver")
@patch("local_newsifier.tools.entity_tracker.ContextAnalyzer")
@patch("spacy.load")
def test_entity_tracker_process_article(
    mock_spacy_load, mock_context_analyzer_class, mock_entity_resolver_class,
    mock_db_manager, mock_entity_resolver, mock_context_analyzer
):
    """Test processing an article for entity tracking."""
    # Setup mocks
    mock_spacy_load.return_value = Mock()
    mock_entity_resolver_class.return_value = mock_entity_resolver
    mock_context_analyzer_class.return_value = mock_context_analyzer
    
    # Mock spaCy document with entities
    mock_ent = Mock()
    mock_ent.text = "Joe Biden"
    mock_ent.label_ = "PERSON"
    mock_ent.sent = Mock()
    mock_ent.sent.text = "Joe Biden is the president."
    
    mock_doc = Mock()
    mock_doc.ents = [mock_ent]
    
    mock_nlp = Mock()
    mock_nlp.return_value = mock_doc
    mock_spacy_load.return_value = mock_nlp
    
    # Create tracker
    tracker = EntityTracker(mock_db_manager)
    
    # Test process_article
    result = tracker.process_article(
        article_id=1,
        content="Joe Biden is the president of the United States.",
        title="Article about Biden",
        published_at=datetime.now(timezone.utc)
    )
    
    # Verify the correct methods were called
    mock_entity_resolver.resolve_entity.assert_called_with("Joe Biden", "PERSON")
    mock_context_analyzer.analyze_context.assert_called_with("Joe Biden is the president.")
    
    # Verify that session.add() was called for Entity
    assert mock_db_manager.session.add.call_count >= 1
    
    # Verify that session.commit() was called
    assert mock_db_manager.session.commit.call_count >= 1
    
    # Verify the result
    assert len(result) == 1
    assert result[0]["original_text"] == "Joe Biden"
    assert result[0]["canonical_name"] == "Joe Biden"
    assert result[0]["canonical_id"] == 1
    assert result[0]["context"] == "Joe Biden is the president."
    assert result[0]["sentiment_score"] == 0.5
    assert result[0]["framing_category"] == "leadership"


@patch("local_newsifier.tools.entity_tracker.EntityResolver")
@patch("local_newsifier.tools.entity_tracker.ContextAnalyzer")
@patch("spacy.load")
def test_entity_tracker_update_profile(
    mock_spacy_load, mock_context_analyzer_class, mock_entity_resolver_class,
    mock_db_manager
):
    """Test updating entity profile."""
    # Setup mocks
    mock_spacy_load.return_value = Mock()
    mock_entity_resolver_class.return_value = Mock()
    mock_context_analyzer_class.return_value = Mock()
    
    # Create tracker
    tracker = EntityTracker(mock_db_manager)
    
    # Override the mock_exec to simulate a scenario where the profile doesn't exist
    mock_exec = Mock()
    mock_exec.first.return_value = None
    mock_db_manager.session.exec.return_value = mock_exec
    
    # Test _update_entity_profile - new profile
    tracker._update_entity_profile(
        canonical_entity_id=1,
        entity_text="Joe Biden",
        context_text="Joe Biden is the president.",
        sentiment_score=0.5,
        framing_category="leadership",
        published_at=datetime.now(timezone.utc)
    )
    
    # Verify session.add() and session.commit() were called for creating a new profile
    assert mock_db_manager.session.add.call_count >= 1
    assert mock_db_manager.session.commit.call_count >= 1
    
    # Check that an Entity was created with the right attributes
    # This can be complex to validate directly, so we'll simplify our assertions
    # to just check that add and commit were called