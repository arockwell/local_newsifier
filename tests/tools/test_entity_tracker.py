"""Tests for the Entity Tracker tool."""

from datetime import datetime, timezone
from unittest.mock import Mock, patch
import pytest
from sqlmodel import Session

from local_newsifier.models.entity import Entity
from local_newsifier.models.entity_tracking import (CanonicalEntity,
                                                  EntityMentionContext,
                                                  EntityProfile)
from local_newsifier.tools.entity_tracker import EntityTracker


# Create mock spaCy models that can be used without installing the real models
class MockSpacyModel:
    """Mock spaCy model for testing."""
    
    def __init__(self):
        """Initialize with needed components."""
        self.vocab = Mock()
        self.pipeline = []
        self.ner = Mock()
        self.ner.return_value = []
    
    def __call__(self, text):
        """Process text and return a mock Doc."""
        return Mock(ents=[])


# Replace actual spaCy loading with mock
@pytest.fixture(autouse=True)
def mock_spacy(monkeypatch):
    """Automatically mock spaCy for all tests in this module."""
    mock_model = MockSpacyModel()
    monkeypatch.setattr("spacy.load", lambda model_name: mock_model)


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


@patch("local_newsifier.tools.entity_tracker.EntityTracker.process_article")
def test_entity_tracker_process_article_calls(mock_process_article):
    """Test that process_article can be called correctly with session."""
    # Setup mock
    mock_process_article.return_value = [
        {
            "original_text": "Joe Biden",
            "canonical_name": "Joe Biden",
            "canonical_id": 1,
            "context": "Joe Biden is the president.",
            "sentiment_score": 0.5,
            "framing_category": "leadership"
        }
    ]
    
    # Create tracker and call the mocked method
    tracker = EntityTracker()
    result = tracker.process_article(
        article_id=1,
        content="Test content",
        title="Test title",
        published_at=datetime.now(timezone.utc)
    )
    
    # Verify it was called and returned what we expected
    mock_process_article.assert_called_once()
    assert len(result) == 1
    assert result[0]["original_text"] == "Joe Biden"


@patch("local_newsifier.crud.entity.entity.create")
@patch("local_newsifier.crud.entity_mention_context.entity_mention_context.create")
@patch("local_newsifier.tools.entity_resolver.EntityResolver.resolve_entity")
@patch("local_newsifier.tools.context_analyzer.ContextAnalyzer.analyze_context")
@patch("spacy.load")
def test_entity_tracker_processing_with_mocks(
    mock_spacy_load, mock_analyze_context, mock_resolve_entity, 
    mock_add_mention, mock_add_entity
):
    """Test entity tracking with mocked components."""
    # Mock spaCy
    mock_nlp = Mock()
    mock_ent = Mock()
    mock_ent.text = "Joe Biden"
    mock_ent.label_ = "PERSON"
    mock_ent.sent = Mock()
    mock_ent.sent.text = "Joe Biden is the president."
    
    mock_doc = Mock()
    mock_doc.ents = [mock_ent]
    mock_nlp.return_value = mock_doc
    mock_spacy_load.return_value = mock_nlp
    
    # Mock context analysis
    mock_analyze_context.return_value = {
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
        }
    }
    
    # Mock entity resolution
    mock_resolve_entity.return_value = CanonicalEntity(
        id=1,
        name="Joe Biden",
        entity_type="PERSON",
        description=None,
        entity_metadata={},
        first_seen=datetime.now(timezone.utc),
        last_seen=datetime.now(timezone.utc)
    )
    
    # Mock database operations
    mock_add_entity.return_value = Entity(
        id=1,
        article_id=1,
        text="Joe Biden",
        entity_type="PERSON",
        confidence=0.95
    )
    
    # Create tracker and test process_article
    with patch("local_newsifier.crud.entity_profile.entity_profile.get_by_entity") as mock_get_profile:
        with patch("local_newsifier.crud.entity_profile.entity_profile.create") as mock_add_profile:
            # Set up mock_get_profile to return None (no existing profile)
            mock_get_profile.return_value = None
            
            tracker = EntityTracker()
            result = tracker.process_article(
                article_id=1,
                content="Joe Biden is the president.",
                title="Article about Biden",
                published_at=datetime.now(timezone.utc)
            )
            
            # Verify basic behavior
            assert len(result) == 1
            assert result[0]["original_text"] == "Joe Biden"
            assert result[0]["canonical_name"] == "Joe Biden"
            assert result[0]["sentiment_score"] == 0.5
            
            # Verify mocks were called
            mock_resolve_entity.assert_called_once()
            mock_analyze_context.assert_called_once()
            mock_add_entity.assert_called_once()
            mock_add_mention.assert_called_once()
            mock_get_profile.assert_called_once()
            mock_add_profile.assert_called_once()


@patch("local_newsifier.crud.entity_profile.entity_profile.get_by_entity")
@patch("local_newsifier.crud.entity_profile.entity_profile.create")
@patch("spacy.load")
def test_entity_tracker_update_profile_new(
    mock_spacy_load, mock_add_profile, mock_get_profile
):
    """Test updating entity profile when none exists."""
    # Mock spaCy
    mock_spacy_load.return_value = Mock()
    
    # Mock get_entity_profile to return None (no existing profile)
    mock_get_profile.return_value = None
    
    # Create tracker and test _update_entity_profile
    tracker = EntityTracker()
    tracker._update_entity_profile(
        canonical_entity_id=1,
        entity_text="Joe Biden",
        context_text="Joe Biden is the president.",
        sentiment_score=0.5,
        framing_category="leadership",
        published_at=datetime.now(timezone.utc)
    )
    
    # Verify mocks were called correctly
    mock_get_profile.assert_called_once()
    mock_add_profile.assert_called_once()
    
    # Verify profile data - for CRUD operations, the first parameter is the session
    # and the second parameter (as a keyword arg) is the actual data
    obj_in = mock_add_profile.call_args[1]["obj_in"]
    assert obj_in.canonical_entity_id == 1
    assert obj_in.content is not None  # Check that content field exists
    assert "Joe Biden" in obj_in.content  # Verify content includes entity name
    assert obj_in.profile_metadata["mention_count"] == 1
    assert len(obj_in.profile_metadata["contexts"]) == 1
    assert obj_in.profile_metadata["temporal_data"] is not None


@patch("local_newsifier.crud.entity_profile.entity_profile.get_by_entity")
@patch("local_newsifier.crud.entity_profile.entity_profile.update_or_create")
@patch("spacy.load")
def test_entity_tracker_update_profile_existing(
    mock_spacy_load, mock_update_profile, mock_get_profile
):
    """Test updating entity profile when one already exists."""
    # Mock spaCy
    mock_spacy_load.return_value = Mock()
    
    # Mock get_entity_profile to return an existing profile
    existing_profile = EntityProfile(
        id=1,
        canonical_entity_id=1,
        profile_type="summary",
        content="This is a summary of Joe Biden, a politician.",  # Added required field
        profile_metadata={
            "mention_count": 2,
            "contexts": ["Previous context"],
            "temporal_data": {"2025-04-15": 2},
            "sentiment_scores": {
                "latest": 0.3,
                "average": 0.3
            },
            "framing_categories": {
                "latest": "controversy",
                "history": ["controversy", "controversy"]
            }
        },
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    mock_get_profile.return_value = existing_profile
    
    # Create tracker and test _update_entity_profile
    tracker = EntityTracker()
    tracker._update_entity_profile(
        canonical_entity_id=1,
        entity_text="Joe Biden",
        context_text="Joe Biden is the president.",
        sentiment_score=0.5,
        framing_category="leadership",
        published_at=datetime.now(timezone.utc)
    )
    
    # Verify mocks were called correctly
    mock_get_profile.assert_called_once()
    mock_update_profile.assert_called_once()
    
    # Verify profile data - for CRUD operations, the first parameter is the session
    # and the second parameter (as a keyword arg) is the actual data
    obj_in = mock_update_profile.call_args[1]["obj_in"]
    assert obj_in.canonical_entity_id == 1
    assert obj_in.profile_metadata["mention_count"] == 3  # Increased by 1
    assert len(obj_in.profile_metadata["contexts"]) == 2  # Added one
    assert "leadership" in obj_in.profile_metadata["framing_categories"]["history"]
