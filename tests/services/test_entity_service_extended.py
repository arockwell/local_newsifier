"""Extended tests for the EntityService."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch, ANY

from local_newsifier.models.state import (
    EntityTrackingState, EntityBatchTrackingState, 
    EntityDashboardState, EntityRelationshipState, 
    TrackingStatus
)


def test_process_article_entities_with_multiple_entity_types():
    """Test extraction of different entity types."""
    # Arrange
    # Mock the entity extractor to return multiple entity types
    mock_entity_extractor = MagicMock()
    mock_entity_extractor.extract_entities.return_value = [
        {
            "text": "John Doe", 
            "type": "PERSON", 
            "context": "John Doe visited Chicago.",
            "start_char": 0,
            "end_char": 8
        },
        {
            "text": "Chicago", 
            "type": "LOCATION", 
            "context": "John Doe visited Chicago.",
            "start_char": 18,
            "end_char": 25
        },
        {
            "text": "Microsoft", 
            "type": "ORGANIZATION", 
            "context": "He works at Microsoft.",
            "start_char": 0,
            "end_char": 9
        }
    ]
    
    # Mock context analyzer
    mock_context_analyzer = MagicMock()
    mock_context_analyzer.analyze_context.return_value = {
        "sentiment": {"score": 0.5, "category": "positive"},
        "framing": {"category": "neutral"}
    }
    
    # Mock entity resolver
    mock_entity_resolver = MagicMock()
    # Configure resolver to return different results for each entity
    mock_entity_resolver.resolve_entity.side_effect = [
        {
            "name": "John Doe",
            "entity_type": "PERSON",
            "is_new": True,
            "confidence": 1.0,
            "original_text": "John Doe"
        },
        {
            "name": "Chicago",
            "entity_type": "LOCATION",
            "is_new": True,
            "confidence": 1.0,
            "original_text": "Chicago"
        },
        {
            "name": "Microsoft Corporation",  # Normalized name
            "entity_type": "ORGANIZATION",
            "is_new": False,  # Existing entity
            "confidence": 0.9,
            "original_text": "Microsoft"
        }
    ]
    
    # Mock CRUD operations
    mock_entity_crud = MagicMock()
    mock_entity_crud.create.side_effect = [
        MagicMock(id=1),
        MagicMock(id=2),
        MagicMock(id=3)
    ]
    
    mock_canonical_entity_crud = MagicMock()
    mock_canonical_entity_crud.get_all.return_value = [
        MagicMock(id=42, name="Microsoft Corporation", entity_type="ORGANIZATION")
    ]
    # First two entities are new, third one exists
    mock_canonical_entity_crud.create.side_effect = [
        MagicMock(id=10, name="John Doe"),
        MagicMock(id=11, name="Chicago")
    ]
    mock_canonical_entity_crud.get_by_name.return_value = MagicMock(
        id=42, name="Microsoft Corporation"
    )
    
    mock_entity_mention_context_crud = MagicMock()
    mock_entity_profile_crud = MagicMock()
    mock_article_crud = MagicMock()
    
    # Mock session for container
    mock_session = MagicMock()
    mock_session_context = MagicMock()
    mock_session_context.__enter__ = MagicMock(return_value=mock_session)
    mock_session_context.__exit__ = MagicMock(return_value=None)
    
    # Create container mock
    mock_container = MagicMock()
    mock_container.get.return_value = mock_session_context
    
    # Create the service with mocks
    with patch('local_newsifier.database.session_utils.get_db_session', return_value=mock_session_context):
        from local_newsifier.services.entity_service import EntityService
        service = EntityService(
            entity_crud=mock_entity_crud,
            canonical_entity_crud=mock_canonical_entity_crud,
            entity_mention_context_crud=mock_entity_mention_context_crud,
            entity_profile_crud=mock_entity_profile_crud,
            article_crud=mock_article_crud,
            entity_extractor=mock_entity_extractor,
            context_analyzer=mock_context_analyzer,
            entity_resolver=mock_entity_resolver,
            container=mock_container
        )
    
    # Act
    result = service.process_article_entities(
        article_id=1,
        content="John Doe visited Chicago. He works at Microsoft.",
        title="Test Article",
        published_at=datetime(2025, 1, 1)
    )
    
    # Assert
    # Verify entity extractor was called
    mock_entity_extractor.extract_entities.assert_called_once_with(
        "John Doe visited Chicago. He works at Microsoft."
    )
    
    # Verify context analyzer was called for each entity
    assert mock_context_analyzer.analyze_context.call_count == 3
    
    # Verify entity resolver was called for each entity
    assert mock_entity_resolver.resolve_entity.call_count == 3
    
    # Verify canonical entity operations
    # Two new entities should be created
    assert mock_canonical_entity_crud.create.call_count == 2
    # One existing entity should be retrieved
    assert mock_canonical_entity_crud.get_by_name.call_count == 1
    
    # Verify entity creation
    assert mock_entity_crud.create.call_count == 3
    
    # Verify entity mention context creation
    assert mock_entity_mention_context_crud.create.call_count == 3
    
    # Verify result
    assert len(result) == 3
    
        # Check entity types in result
    entity_types = [str(entity["canonical_name"]) for entity in result]
    assert "John Doe" in entity_types or any("John Doe" in str(name) for name in entity_types)
    assert "Chicago" in entity_types or any("Chicago" in str(name) for name in entity_types)
    assert "Microsoft Corporation" in entity_types or any("Microsoft Corporation" in str(name) for name in entity_types)


def test_entity_resolution_with_ambiguous_entities():
    """Test resolution of ambiguous entities."""
    # Arrange
    # Mock the entity extractor
    mock_entity_extractor = MagicMock()
    mock_entity_extractor.extract_entities.return_value = [
        {
            "text": "Washington", 
            "type": "AMBIGUOUS", 
            "context": "Washington signed the bill.",
            "start_char": 0,
            "end_char": 10
        },
        {
            "text": "Washington", 
            "type": "AMBIGUOUS", 
            "context": "He visited Washington last week.",
            "start_char": 11,
            "end_char": 21
        }
    ]
    
    # Mock context analyzer
    mock_context_analyzer = MagicMock()
    mock_context_analyzer.analyze_context.return_value = {
        "sentiment": {"score": 0.5, "category": "positive"},
        "framing": {"category": "neutral"}
    }
    
    # Mock entity resolver to resolve ambiguous entities
    mock_entity_resolver = MagicMock()
    # First "Washington" is a person, second is a location
    mock_entity_resolver.resolve_entity.side_effect = [
        {
            "name": "George Washington",
            "entity_type": "PERSON",
            "is_new": False,
            "confidence": 0.8,
            "original_text": "Washington"
        },
        {
            "name": "Washington, D.C.",
            "entity_type": "LOCATION",
            "is_new": False,
            "confidence": 0.9,
            "original_text": "Washington"
        }
    ]
    
    # Mock CRUD operations
    mock_entity_crud = MagicMock()
    mock_entity_crud.create.side_effect = [MagicMock(id=1), MagicMock(id=2)]
    
    mock_canonical_entity_crud = MagicMock()
    mock_canonical_entity_crud.get_all.return_value = [
        MagicMock(id=101, name="George Washington", entity_type="PERSON"),
        MagicMock(id=102, name="Washington, D.C.", entity_type="LOCATION")
    ]
    # Both entities exist, so get_by_name will be called
    mock_canonical_entity_crud.get_by_name.side_effect = [
        MagicMock(id=101, name="George Washington"),
        MagicMock(id=102, name="Washington, D.C.")
    ]
    
    mock_entity_mention_context_crud = MagicMock()
    mock_entity_profile_crud = MagicMock()
    mock_article_crud = MagicMock()
    
    # Mock session for container
    mock_session = MagicMock()
    mock_session_context = MagicMock()
    mock_session_context.__enter__ = MagicMock(return_value=mock_session)
    mock_session_context.__exit__ = MagicMock(return_value=None)
    
    # Create container mock
    mock_container = MagicMock()
    mock_container.get.return_value = mock_session_context
    
    # Create the service with mocks
    with patch('local_newsifier.database.session_utils.get_db_session', return_value=mock_session_context):
        from local_newsifier.services.entity_service import EntityService
        service = EntityService(
            entity_crud=mock_entity_crud,
            canonical_entity_crud=mock_canonical_entity_crud,
            entity_mention_context_crud=mock_entity_mention_context_crud,
            entity_profile_crud=mock_entity_profile_crud,
            article_crud=mock_article_crud,
            entity_extractor=mock_entity_extractor,
            context_analyzer=mock_context_analyzer,
            entity_resolver=mock_entity_resolver,
            container=mock_container
        )
    
    # Act
    result = service.process_article_entities(
        article_id=1,
        content="Washington signed the bill. He visited Washington last week.",
        title="Test Article",
        published_at=datetime(2025, 1, 1)
    )
    
    # Assert
    # Verify entity resolver was called for each entity
    assert mock_entity_resolver.resolve_entity.call_count == 2
    
    # Verify canonical entity retrieval
    assert mock_canonical_entity_crud.get_by_name.call_count == 2
    
    # Verify entity creation
    assert mock_entity_crud.create.call_count == 2
    
    # Verify result
    assert len(result) == 2
    
        # Check that the same text was resolved to different entities
    assert "George Washington" in str(result[0]["canonical_name"])
    assert "Washington, D.C." in str(result[1]["canonical_name"])


def test_process_article_with_empty_content():
    """Test handling of empty content."""
    # Arrange
    # Mock the entity extractor to return empty list for empty content
    mock_entity_extractor = MagicMock()
    mock_entity_extractor.extract_entities.return_value = []
    
    # Mock other dependencies
    mock_context_analyzer = MagicMock()
    mock_entity_resolver = MagicMock()
    
    mock_entity_crud = MagicMock()
    mock_canonical_entity_crud = MagicMock()
    mock_canonical_entity_crud.get_all.return_value = []
    
    mock_entity_mention_context_crud = MagicMock()
    mock_entity_profile_crud = MagicMock()
    mock_article_crud = MagicMock()
    
    # Mock session factory
    mock_session = MagicMock()
    mock_session_factory = MagicMock(
        return_value=MagicMock(
            __enter__=MagicMock(return_value=mock_session), 
            __exit__=MagicMock()
        )
    )
    
    # Create the service with mocks
    from local_newsifier.services.entity_service import EntityService
    service = EntityService(
        entity_crud=mock_entity_crud,
        canonical_entity_crud=mock_canonical_entity_crud,
        entity_mention_context_crud=mock_entity_mention_context_crud,
        entity_profile_crud=mock_entity_profile_crud,
        article_crud=mock_article_crud,
        entity_extractor=mock_entity_extractor,
        context_analyzer=mock_context_analyzer,
        entity_resolver=mock_entity_resolver,
        session_factory=mock_session_factory
    )
    
    # Act
    # Test with empty content
    result = service.process_article_entities(
        article_id=1,
        content="",
        title="Empty Article",
        published_at=datetime(2025, 1, 1)
    )
    
    # Assert
    # Verify entity extractor was called with empty string
    mock_entity_extractor.extract_entities.assert_called_once_with("")
    
    # Verify no other processing occurred
    mock_context_analyzer.analyze_context.assert_not_called()
    mock_entity_resolver.resolve_entity.assert_not_called()
    mock_entity_crud.create.assert_not_called()
    mock_entity_mention_context_crud.create.assert_not_called()
    
    # Verify empty result
    assert len(result) == 0


def test_entity_relationship_with_complex_network():
    """Test identification of complex entity relationships."""
    # Arrange
    # Mock canonical entity CRUD
    mock_canonical_entity_crud = MagicMock()
    
    # Create a mock entity
    mock_entity = MagicMock(
        id=1, 
        name="Apple Inc.", 
        entity_type="ORGANIZATION"
    )
    mock_canonical_entity_crud.get.return_value = mock_entity
    
    # Create mock articles mentioning this entity
    mock_article1 = MagicMock(id=101)
    mock_article2 = MagicMock(id=102)
    mock_article3 = MagicMock(id=103)
    mock_canonical_entity_crud.get_articles_mentioning_entity.return_value = [
        mock_article1, mock_article2, mock_article3
    ]
    
    # Mock entity CRUD to return different entities for each article
    mock_entity_crud = MagicMock()
    # Article 1: Apple and Microsoft
    # Article 2: Apple, Microsoft, and Google
    # Article 3: Apple and Samsung
    mock_entity_crud.get_by_article.side_effect = [
        [
            MagicMock(text="Apple Inc.", entity_type="ORGANIZATION"),
            MagicMock(text="Microsoft", entity_type="ORGANIZATION")
        ],
        [
            MagicMock(text="Apple Inc.", entity_type="ORGANIZATION"),
            MagicMock(text="Microsoft", entity_type="ORGANIZATION"),
            MagicMock(text="Google", entity_type="ORGANIZATION")
        ],
        [
            MagicMock(text="Apple Inc.", entity_type="ORGANIZATION"),
            MagicMock(text="Samsung", entity_type="ORGANIZATION")
        ]
    ]
    
    # Mock canonical entity retrieval for co-occurring entities
    mock_canonical_entity_crud.get_by_name.side_effect = [
        MagicMock(id=2, name="Microsoft", entity_type="ORGANIZATION"),  # Article 1
        mock_entity,  # Article 1 - Apple (skipped)
        MagicMock(id=2, name="Microsoft", entity_type="ORGANIZATION"),  # Article 2
        mock_entity,  # Article 2 - Apple (skipped)
        MagicMock(id=3, name="Google", entity_type="ORGANIZATION"),     # Article 2
        MagicMock(id=4, name="Samsung", entity_type="ORGANIZATION"),    # Article 3
        mock_entity   # Article 3 - Apple (skipped)
    ]
    
    # Mock other dependencies
    mock_entity_mention_context_crud = MagicMock()
    mock_entity_profile_crud = MagicMock()
    mock_article_crud = MagicMock()
    
    mock_entity_extractor = MagicMock()
    mock_context_analyzer = MagicMock()
    mock_entity_resolver = MagicMock()
    
    # Mock session factory
    mock_session = MagicMock()
    mock_session_factory = MagicMock(
        return_value=MagicMock(
            __enter__=MagicMock(return_value=mock_session), 
            __exit__=MagicMock()
        )
    )
    
    # Create the service with mocks
    from local_newsifier.services.entity_service import EntityService
    service = EntityService(
        entity_crud=mock_entity_crud,
        canonical_entity_crud=mock_canonical_entity_crud,
        entity_mention_context_crud=mock_entity_mention_context_crud,
        entity_profile_crud=mock_entity_profile_crud,
        article_crud=mock_article_crud,
        entity_extractor=mock_entity_extractor,
        context_analyzer=mock_context_analyzer,
        entity_resolver=mock_entity_resolver,
        session_factory=mock_session_factory
    )
    
    # Create relationship state
    state = EntityRelationshipState(entity_id=1, days=30)
    
    # Act
    result_state = service.find_entity_relationships(state)
    
    # Assert
    # Verify success
    assert result_state.status == TrackingStatus.SUCCESS
    
    # Verify relationships data
    assert "relationship_data" in result_state.__dict__
    assert "relationships" in result_state.relationship_data
    
    # We should have 3 relationships (Microsoft, Google, Samsung)
    assert len(result_state.relationship_data["relationships"]) == 3
    
        # Microsoft should be first (appeared in 2 articles)
    assert "Microsoft" in str(result_state.relationship_data["relationships"][0]["entity_name"])
    assert result_state.relationship_data["relationships"][0]["co_occurrence_count"] == 2
    
    # Google and Samsung should each appear in 1 article
    google_relationship = next(r for r in result_state.relationship_data["relationships"] 
                          if "Google" in str(r["entity_name"]))
    assert google_relationship["co_occurrence_count"] == 1
    
    samsung_relationship = next(r for r in result_state.relationship_data["relationships"] 
                           if "Samsung" in str(r["entity_name"]))
    assert samsung_relationship["co_occurrence_count"] == 1


def test_dashboard_generation_with_filters():
    """Test dashboard generation with various filters."""
    # Arrange
    # Mock canonical entity CRUD
    mock_canonical_entity_crud = MagicMock()
    
    # Create mock entities of different types
    mock_person1 = MagicMock(
        id=1, 
        name="John Doe", 
        entity_type="PERSON",
        first_seen=datetime(2025, 1, 1, tzinfo=timezone.utc),
        last_seen=datetime(2025, 1, 10, tzinfo=timezone.utc)
    )
    mock_person2 = MagicMock(
        id=2, 
        name="Jane Smith", 
        entity_type="PERSON",
        first_seen=datetime(2025, 1, 2, tzinfo=timezone.utc),
        last_seen=datetime(2025, 1, 15, tzinfo=timezone.utc)
    )
    
    # Return only PERSON entities
    mock_canonical_entity_crud.get_by_type.return_value = [mock_person1, mock_person2]
    
    # Mock mention counts
    mock_canonical_entity_crud.get_mentions_count.side_effect = [15, 8]
    
    # Mock timelines
    mock_canonical_entity_crud.get_entity_timeline.side_effect = [
        [
            {"date": datetime(2025, 1, 10, tzinfo=timezone.utc), "count": 5},
            {"date": datetime(2025, 1, 5, tzinfo=timezone.utc), "count": 7},
            {"date": datetime(2025, 1, 1, tzinfo=timezone.utc), "count": 3}
        ],
        [
            {"date": datetime(2025, 1, 15, tzinfo=timezone.utc), "count": 3},
            {"date": datetime(2025, 1, 10, tzinfo=timezone.utc), "count": 2},
            {"date": datetime(2025, 1, 2, tzinfo=timezone.utc), "count": 3}
        ]
    ]
    
    # Mock sentiment trends
    mock_entity_mention_context_crud = MagicMock()
    mock_entity_mention_context_crud.get_sentiment_trend.side_effect = [
        [
            {"date": "2025-01-10", "sentiment": 0.7},
            {"date": "2025-01-05", "sentiment": 0.5},
            {"date": "2025-01-01", "sentiment": 0.6}
        ],
        [
            {"date": "2025-01-15", "sentiment": 0.4},
            {"date": "2025-01-10", "sentiment": 0.3},
            {"date": "2025-01-02", "sentiment": 0.6}
        ]
    ]
    
    # Mock other dependencies
    mock_entity_crud = MagicMock()
    mock_entity_profile_crud = MagicMock()
    mock_article_crud = MagicMock()
    
    mock_entity_extractor = MagicMock()
    mock_context_analyzer = MagicMock()
    mock_entity_resolver = MagicMock()
    
    # Mock session factory
    mock_session = MagicMock()
    mock_session_factory = MagicMock(
        return_value=MagicMock(
            __enter__=MagicMock(return_value=mock_session), 
            __exit__=MagicMock()
        )
    )
    
    # Create the service with mocks
    from local_newsifier.services.entity_service import EntityService
    service = EntityService(
        entity_crud=mock_entity_crud,
        canonical_entity_crud=mock_canonical_entity_crud,
        entity_mention_context_crud=mock_entity_mention_context_crud,
        entity_profile_crud=mock_entity_profile_crud,
        article_crud=mock_article_crud,
        entity_extractor=mock_entity_extractor,
        context_analyzer=mock_context_analyzer,
        entity_resolver=mock_entity_resolver,
        session_factory=mock_session_factory
    )
    
    # Create dashboard state with filters
    state = EntityDashboardState(days=15, entity_type="PERSON")
    
    # Act
    result_state = service.generate_entity_dashboard(state)
    
    # Assert
    # Verify success
    assert result_state.status == TrackingStatus.SUCCESS
    
    # Verify dashboard data
    assert "dashboard_data" in result_state.__dict__
    assert "entities" in result_state.dashboard_data
    
    # Verify entity count and total mentions
    assert result_state.dashboard_data["entity_count"] == 2
    assert result_state.dashboard_data["total_mentions"] == 23  # 15 + 8
    
    # Verify date range
    assert "date_range" in result_state.dashboard_data
    assert result_state.dashboard_data["date_range"]["days"] == 15
    
    # Verify entities are sorted by mention count
    entities = result_state.dashboard_data["entities"]
    assert len(entities) == 2
    assert "John Doe" in str(entities[0]["name"])
    assert entities[0]["mention_count"] == 15
    assert "Jane Smith" in str(entities[1]["name"])
    assert entities[1]["mention_count"] == 8
    
    # Verify timeline data
    assert len(entities[0]["timeline"]) == 3
    assert entities[0]["timeline"][0]["date"] == datetime(2025, 1, 10, tzinfo=timezone.utc)
    assert entities[0]["timeline"][0]["count"] == 5
    
    # Verify sentiment trend data
    assert len(entities[0]["sentiment_trend"]) == 3
    assert entities[0]["sentiment_trend"][0]["date"] == "2025-01-10"
    assert entities[0]["sentiment_trend"][0]["sentiment"] == 0.7


def test_process_batch_with_empty_article_list():
    """Test batch processing with no articles."""
    # Arrange
    # Mock article CRUD to return empty list
    mock_article_crud = MagicMock()
    mock_article_crud.get_by_status.return_value = []
    
    # Mock other dependencies
    mock_entity_crud = MagicMock()
    mock_canonical_entity_crud = MagicMock()
    mock_entity_mention_context_crud = MagicMock()
    mock_entity_profile_crud = MagicMock()
    
    mock_entity_extractor = MagicMock()
    mock_context_analyzer = MagicMock()
    mock_entity_resolver = MagicMock()
    
    # Mock session factory
    mock_session = MagicMock()
    mock_session_factory = MagicMock(
        return_value=MagicMock(
            __enter__=MagicMock(return_value=mock_session), 
            __exit__=MagicMock()
        )
    )
    
    # Create the service with mocks
    from local_newsifier.services.entity_service import EntityService
    service = EntityService(
        entity_crud=mock_entity_crud,
        canonical_entity_crud=mock_canonical_entity_crud,
        entity_mention_context_crud=mock_entity_mention_context_crud,
        entity_profile_crud=mock_entity_profile_crud,
        article_crud=mock_article_crud,
        entity_extractor=mock_entity_extractor,
        context_analyzer=mock_context_analyzer,
        entity_resolver=mock_entity_resolver,
        session_factory=mock_session_factory
    )
    
    # Create batch state
    state = EntityBatchTrackingState(status_filter="analyzed")
    
    # Act
    result_state = service.process_articles_batch(state)
    
    # Assert
    # Verify success even with empty list
    assert result_state.status == TrackingStatus.SUCCESS
    
    # Verify article count
    assert result_state.total_articles == 0
    assert result_state.processed_count == 0
    assert result_state.error_count == 0
    
    # Verify no articles were processed
    assert len(result_state.processed_articles) == 0
    
    # Verify logs
    assert any("Found 0 articles to process" in log for log in result_state.run_logs)
    assert any("Batch processing completed successfully" in log for log in result_state.run_logs)


def test_process_article_with_very_large_content():
    """Test processing an article with very large content."""
    # Arrange
    # Create a large content string
    large_content = "This is a test article. " * 1000  # Approximately 20KB of text
    
    # Mock the entity extractor to return a few entities from the large content
    mock_entity_extractor = MagicMock()
    mock_entity_extractor.extract_entities.return_value = [
        {
            "text": "Test Entity", 
            "type": "MISC", 
            "context": "This is a test article. Test Entity appears here.",
            "start_char": 16,
            "end_char": 27
        }
    ]
    
    # Mock context analyzer
    mock_context_analyzer = MagicMock()
    mock_context_analyzer.analyze_context.return_value = {
        "sentiment": {"score": 0.5, "category": "neutral"},
        "framing": {"category": "neutral"}
    }
    
    # Mock entity resolver
    mock_entity_resolver = MagicMock()
    mock_entity_resolver.resolve_entity.return_value = {
        "name": "Test Entity",
        "entity_type": "MISC",
        "is_new": True,
        "confidence": 1.0,
        "original_text": "Test Entity"
    }
    
    # Mock CRUD operations
    mock_entity_crud = MagicMock()
    mock_entity_crud.create.return_value = MagicMock(id=1)
    
    mock_canonical_entity_crud = MagicMock()
    mock_canonical_entity_crud.get_all.return_value = []
    mock_canonical_entity_crud.create.return_value = MagicMock(id=1, name="Test Entity")
    
    mock_entity_mention_context_crud = MagicMock()
    mock_entity_profile_crud = MagicMock()
    mock_article_crud = MagicMock()
    
    # Mock session factory
    mock_session = MagicMock()
    mock_session_factory = MagicMock(
        return_value=MagicMock(
            __enter__=MagicMock(return_value=mock_session), 
            __exit__=MagicMock()
        )
    )
    
    # Create the service with mocks
    from local_newsifier.services.entity_service import EntityService
    service = EntityService(
        entity_crud=mock_entity_crud,
        canonical_entity_crud=mock_canonical_entity_crud,
        entity_mention_context_crud=mock_entity_mention_context_crud,
        entity_profile_crud=mock_entity_profile_crud,
        article_crud=mock_article_crud,
        entity_extractor=mock_entity_extractor,
        context_analyzer=mock_context_analyzer,
        entity_resolver=mock_entity_resolver,
        session_factory=mock_session_factory
    )
    
    # Create tracking state
    state = EntityTrackingState(
        article_id=1,
        content=large_content,
        title="Large Article",
        published_at=datetime(2025, 1, 1, tzinfo=timezone.utc)
    )
    
    # Act
    result_state = service.process_article_with_state(state)
    
    # Assert
    # Verify success
    assert result_state.status == TrackingStatus.SUCCESS
    
    # Verify entity extractor was called with the large content
    mock_entity_extractor.extract_entities.assert_called_once_with(large_content)
    
    # Verify entity was processed
    assert len(result_state.entities) == 1
    assert result_state.entities[0]["original_text"] == "Test Entity"
    
    # Verify article status was updated
    mock_article_crud.update_status.assert_called_once_with(
        mock_session, article_id=1, status="entity_tracked"
    )


def test_entity_service_with_custom_session_factory():
    """Test entity service with a custom session factory."""
    # Arrange
    # Create a custom session factory
    custom_session = MagicMock()
    custom_session_factory = MagicMock(
        return_value=MagicMock(
            __enter__=MagicMock(return_value=custom_session), 
            __exit__=MagicMock()
        )
    )
    
    # Mock dependencies
    mock_entity_crud = MagicMock()
    mock_canonical_entity_crud = MagicMock()
    mock_entity_mention_context_crud = MagicMock()
    mock_entity_profile_crud = MagicMock()
    mock_article_crud = MagicMock()
    
    mock_entity_extractor = MagicMock()
    mock_context_analyzer = MagicMock()
    mock_entity_resolver = MagicMock()
    
    # Create the service with custom session factory
    from local_newsifier.services.entity_service import EntityService
    service = EntityService(
        entity_crud=mock_entity_crud,
        canonical_entity_crud=mock_canonical_entity_crud,
        entity_mention_context_crud=mock_entity_mention_context_crud,
        entity_profile_crud=mock_entity_profile_crud,
        article_crud=mock_article_crud,
        entity_extractor=mock_entity_extractor,
        context_analyzer=mock_context_analyzer,
        entity_resolver=mock_entity_resolver,
        session_factory=custom_session_factory
    )
    
    # Create a simple state
    state = EntityTrackingState(
        article_id=1,
        content="Test content",
        title="Test Article",
        published_at=datetime(2025, 1, 1, tzinfo=timezone.utc)
    )
    
    # Mock entity extractor to return an entity
    mock_entity_extractor.extract_entities.return_value = [
        {
            "text": "Test Entity", 
            "type": "MISC", 
            "context": "Test content",
            "start_char": 0,
            "end_char": 11
        }
    ]
    
    # Mock context analyzer
    mock_context_analyzer.analyze_context.return_value = {
        "sentiment": {"score": 0.5, "category": "neutral"},
        "framing": {"category": "neutral"}
    }
    
    # Mock entity resolver
    mock_entity_resolver.resolve_entity.return_value = {
        "name": "Test Entity",
        "entity_type": "MISC",
        "is_new": True,
        "confidence": 1.0,
        "original_text": "Test Entity"
    }
    
    # Mock canonical entity creation
    mock_canonical_entity_crud.get_all.return_value = []
    mock_canonical_entity_crud.create.return_value = MagicMock(id=1, name="Test Entity")
    
    # Mock entity creation
    mock_entity_crud.create.return_value = MagicMock(id=1)
    
    # Act
    result_state = service.process_article_with_state(state)
    
    # Assert
    # Verify custom session factory was used
    custom_session_factory.assert_called()
    
    # Verify success
    assert result_state.status == TrackingStatus.SUCCESS
    
    # Verify entity was processed
    assert len(result_state.entities) == 1
    
    # Verify article status was updated using custom session
    mock_article_crud.update_status.assert_called_once_with(
        custom_session, article_id=1, status="entity_tracked"
    )
