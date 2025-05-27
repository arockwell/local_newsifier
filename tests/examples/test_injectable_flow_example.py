"""Example test for an injectable flow component using the simplified testing approach."""

from typing import Annotated, Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest
from fastapi import Depends

# Create a mock injectable decorator for testing
mock_injectable = MagicMock()


def mock_decorator(use_cache=True):
    def wrapper(func):
        func.__injectable_config = True
        return func

    return wrapper


mock_injectable.side_effect = mock_decorator

# Patch the real injectable with our mock
with patch("fastapi_injectable.injectable", mock_injectable):
    from fastapi_injectable import injectable

# Import testing utilities
from tests.conftest_injectable import (common_injectable_mocks, create_mock_service,
                                       mock_injectable_dependencies)


# Define a simple injectable flow for demonstration purposes
@injectable(use_cache=False)
class ExampleEntityTrackingFlow:
    """Example injectable entity tracking flow for testing."""

    def __init__(
        self,
        entity_service: Annotated[Any, Depends("get_entity_service")],
        article_service: Annotated[Any, Depends("get_article_service")],
        entity_extractor: Annotated[Any, Depends("get_entity_extractor_tool")],
        entity_resolver: Annotated[Any, Depends("get_entity_resolver_tool")],
    ):
        self.entity_service = entity_service
        self.article_service = article_service
        self.entity_extractor = entity_extractor
        self.entity_resolver = entity_resolver

    def process_article(self, article_id: int) -> List[Dict]:
        """Process an article to extract and track entities."""
        # Get article
        article = self.article_service.get_article(article_id)
        if not article:
            return []

        # Extract entities
        entities = self.entity_extractor.extract_entities(article["content"])

        # Save entities to database
        saved_entities = self.entity_service.create_entities(
            article_id=article_id, entities=entities
        )

        # Resolve entities to canonical representations
        canonical_entities = []
        for entity in saved_entities:
            canonical = self.entity_resolver.resolve_entity(entity["id"])
            if canonical:
                canonical_entities.append(canonical)

        return canonical_entities

    def analyze_entity_trends(self, entity_name: str, days: int = 30) -> Dict:
        """Analyze trends for a specific entity over time."""
        # Get all mentions of the entity
        mentions = self.entity_service.get_entity_mentions(entity_name, days=days)

        # Analyze mentions over time
        mention_counts = {}
        for mention in mentions:
            date = mention["date"].strftime("%Y-%m-%d")
            mention_counts[date] = mention_counts.get(date, 0) + 1

        # Get associated entities (co-occurrences)
        associated = self.entity_service.get_associated_entities(entity_name)

        return {
            "entity": entity_name,
            "total_mentions": len(mentions),
            "mention_trend": mention_counts,
            "associated_entities": associated,
        }


class TestExampleEntityTrackingFlow:
    """Tests for the ExampleEntityTrackingFlow."""

    def test_process_article(self, mock_injectable_dependencies):
        """Test processing an article to extract and track entities."""
        # Arrange
        article_id = 1
        article = {
            "id": article_id,
            "title": "Test Article",
            "content": "John Doe visited New York yesterday.",
        }

        extracted_entities = [
            {"text": "John Doe", "entity_type": "PERSON"},
            {"text": "New York", "entity_type": "GPE"},
        ]

        saved_entities = [
            {"id": 1, "text": "John Doe", "entity_type": "PERSON", "article_id": article_id},
            {"id": 2, "text": "New York", "entity_type": "GPE", "article_id": article_id},
        ]

        canonical_entities = [
            {"id": 101, "name": "John Doe", "entity_type": "PERSON"},
            {"id": 102, "name": "New York", "entity_type": "GPE"},
        ]

        # Create mocks
        article_service_mock = MagicMock()
        article_service_mock.get_article.return_value = article

        entity_extractor_mock = MagicMock()
        entity_extractor_mock.extract_entities.return_value = extracted_entities

        entity_service_mock = MagicMock()
        entity_service_mock.create_entities.return_value = saved_entities

        entity_resolver_mock = MagicMock()
        entity_resolver_mock.resolve_entity.side_effect = lambda id: canonical_entities[id - 1]

        # Create flow
        flow = ExampleEntityTrackingFlow(
            entity_service=entity_service_mock,
            article_service=article_service_mock,
            entity_extractor=entity_extractor_mock,
            entity_resolver=entity_resolver_mock,
        )

        # Act
        result = flow.process_article(article_id)

        # Assert
        assert result == canonical_entities
        article_service_mock.get_article.assert_called_once_with(article_id)
        entity_extractor_mock.extract_entities.assert_called_once_with(article["content"])
        entity_service_mock.create_entities.assert_called_once_with(
            article_id=article_id, entities=extracted_entities
        )
        assert entity_resolver_mock.resolve_entity.call_count == 2

    def test_process_article_not_found(self, mock_injectable_dependencies):
        """Test processing an article that doesn't exist."""
        # Arrange - using mock_injectable_dependencies utility
        mock = mock_injectable_dependencies

        article_service_mock = MagicMock()
        article_service_mock.get_article.return_value = None

        entity_service_mock = MagicMock()
        entity_extractor_mock = MagicMock()
        entity_resolver_mock = MagicMock()

        # Register mocks
        mock.register("get_article_service", article_service_mock)
        mock.register("get_entity_service", entity_service_mock)
        mock.register("get_entity_extractor_tool", entity_extractor_mock)
        mock.register("get_entity_resolver_tool", entity_resolver_mock)

        # Create flow
        flow = ExampleEntityTrackingFlow(
            entity_service=mock.get("get_entity_service"),
            article_service=mock.get("get_article_service"),
            entity_extractor=mock.get("get_entity_extractor_tool"),
            entity_resolver=mock.get("get_entity_resolver_tool"),
        )

        # Act
        result = flow.process_article(999)  # Non-existent article

        # Assert
        assert result == []
        article_service_mock.get_article.assert_called_once_with(999)
        entity_extractor_mock.extract_entities.assert_not_called()
        entity_service_mock.create_entities.assert_not_called()
        entity_resolver_mock.resolve_entity.assert_not_called()

    def test_analyze_entity_trends(self, mock_injectable_dependencies):
        """Test analyzing entity trends."""
        # Arrange
        entity_name = "John Doe"
        days = 7

        # Create mock services directly
        entity_service_mock = MagicMock()
        article_service_mock = MagicMock()
        entity_extractor_mock = MagicMock()
        entity_resolver_mock = MagicMock()

        # Mock mentions with different dates
        from datetime import datetime, timedelta

        today = datetime.now()
        mentions = [
            {"id": 1, "entity_name": entity_name, "date": today - timedelta(days=1)},
            {"id": 2, "entity_name": entity_name, "date": today - timedelta(days=1)},
            {"id": 3, "entity_name": entity_name, "date": today - timedelta(days=3)},
        ]
        entity_service_mock.get_entity_mentions.return_value = mentions

        # Mock associated entities
        associated = [
            {"entity": "Jane Doe", "count": 5},
            {"entity": "New York", "count": 3},
        ]
        entity_service_mock.get_associated_entities.return_value = associated

        # Create flow with direct mocks
        flow = ExampleEntityTrackingFlow(
            entity_service=entity_service_mock,
            article_service=article_service_mock,
            entity_extractor=entity_extractor_mock,
            entity_resolver=entity_resolver_mock,
        )

        # Act
        result = flow.analyze_entity_trends(entity_name, days)

        # Assert
        assert result["entity"] == entity_name
        assert result["total_mentions"] == 3

        # Check that we have 2 days with mentions in the trend data
        assert len(result["mention_trend"]) == 2

        # Check associated entities
        assert result["associated_entities"] == associated

        # Verify the calls
        entity_service_mock.get_entity_mentions.assert_called_once_with(entity_name, days=days)
        entity_service_mock.get_associated_entities.assert_called_once_with(entity_name)
