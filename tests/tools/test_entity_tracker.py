"""Tests for the Entity Tracker tool."""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest

from local_newsifier.database.manager import DatabaseManager
from local_newsifier.models.pydantic_models import Entity, EntityCreate
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
    
    # Mock add_entity
    def add_entity(entity_data):
        return Entity(
            id=1,
            article_id=entity_data.article_id,
            text=entity_data.text,
            entity_type=entity_data.entity_type,
            confidence=entity_data.confidence
        )
    
    db_manager.add_entity.side_effect = add_entity
    
    # Mock add_entity_mention_context
    db_manager.add_entity_mention_context.return_value = Mock()
    
    # Mock get_entity_profile
    db_manager.get_entity_profile.return_value = None
    
    # Mock add_entity_profile
    db_manager.add_entity_profile.return_value = Mock()
    
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
    mock_db_manager.add_entity.assert_called_once()
    mock_db_manager.add_entity_mention_context.assert_called_once()
    mock_db_manager.get_entity_profile.assert_called_with(1)
    mock_db_manager.add_entity_profile.assert_called_once()
    
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
    
    # Test _update_entity_profile - new profile
    tracker._update_entity_profile(
        canonical_entity_id=1,
        entity_text="Joe Biden",
        context_text="Joe Biden is the president.",
        sentiment_score=0.5,
        framing_category="leadership",
        published_at=datetime.now(timezone.utc)
    )
    
    # Verify profile was created
    mock_db_manager.get_entity_profile.assert_called_with(1)
    mock_db_manager.add_entity_profile.assert_called_once()
    
    # Verify profile data
    profile_data = mock_db_manager.add_entity_profile.call_args[0][0]
    assert profile_data.canonical_entity_id == 1
    assert profile_data.mention_count == 1
    assert len(profile_data.contexts) == 1
    assert profile_data.contexts[0] == "Joe Biden is the president."
    assert profile_data.temporal_data is not None