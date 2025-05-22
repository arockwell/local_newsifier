"""Tests for the trend models."""

from datetime import datetime, timezone
from uuid import UUID

import pytest

from src.local_newsifier.models.trend import (
    TimeFrame,
    TopicFrequency,
    TrendAnalysis,
    TrendEntity,
    TrendEvidenceItem,
    TrendStatus,
    TrendType,
)


def test_topic_frequency_model():
    """Test the TopicFrequency model."""
    # Create a TopicFrequency object
    topic_freq = TopicFrequency(
        topic="Downtown Development",
        entity_type="ORG",
        frequencies={"2023-01-01": 2, "2023-01-02": 3},
        total_mentions=5,
    )

    # Test initial state
    assert topic_freq.topic == "Downtown Development"
    assert topic_freq.entity_type == "ORG"
    assert topic_freq.frequencies == {"2023-01-01": 2, "2023-01-02": 3}
    assert topic_freq.total_mentions == 5

    # Test adding occurrences with date string
    topic_freq.add_occurrence("2023-01-03", 2)
    assert topic_freq.frequencies["2023-01-03"] == 2
    assert topic_freq.total_mentions == 7

    # Test adding occurrences with datetime
    dt = datetime(2023, 1, 4, 12, 0, 0, tzinfo=timezone.utc)
    topic_freq.add_occurrence(dt)
    assert topic_freq.frequencies["2023-01-04"] == 1
    assert topic_freq.total_mentions == 8

    # Test updating existing date
    topic_freq.add_occurrence("2023-01-01")
    assert topic_freq.frequencies["2023-01-01"] == 3
    assert topic_freq.total_mentions == 9


def test_trend_evidence_item_model():
    """Test the TrendEvidenceItem model."""
    # Create evidence item
    dt = datetime(2023, 1, 15, 12, 30, 0, tzinfo=timezone.utc)
    evidence = TrendEvidenceItem(
        article_id=123,
        article_url="https://example.com/news/article1",
        article_title="Test Article",
        published_at=dt,
        evidence_text="Example text about the trend",
        relevance_score=0.85,
    )

    # Test attributes
    assert evidence.article_id == 123
    assert evidence.article_url == "https://example.com/news/article1"
    assert evidence.article_title == "Test Article"
    assert evidence.published_at == dt
    assert evidence.evidence_text == "Example text about the trend"
    assert evidence.relevance_score == 0.85


def test_trend_entity_model():
    """Test the TrendEntity model."""
    # Create trend entity
    entity = TrendEntity(
        text="Mayor Johnson",
        entity_type="PERSON",
        frequency=5,
        relevance_score=0.9,
    )

    # Test attributes
    assert entity.text == "Mayor Johnson"
    assert entity.entity_type == "PERSON"
    assert entity.frequency == 5
    assert entity.relevance_score == 0.9


def test_trend_analysis_model():
    """Test the TrendAnalysis model."""
    # Create trend analysis
    start_date = datetime(2023, 1, 15, tzinfo=timezone.utc)
    trend = TrendAnalysis(
        trend_type=TrendType.EMERGING_TOPIC,
        name="Downtown Development",
        description="Increasing coverage of downtown development project",
        status=TrendStatus.CONFIRMED,
        confidence_score=0.85,
        start_date=start_date,
        frequency_data={"2023-01-15": 2, "2023-01-16": 3},
        statistical_significance=1.8,
        tags=["development", "local-government"],
    )

    # Test initial state
    assert isinstance(trend.trend_id, UUID)
    assert trend.trend_type == TrendType.EMERGING_TOPIC
    assert trend.name == "Downtown Development"
    assert trend.description == "Increasing coverage of downtown development project"
    assert trend.status == TrendStatus.CONFIRMED
    assert trend.confidence_score == 0.85
    assert trend.start_date == start_date
    assert trend.end_date is None
    assert trend.frequency_data == {"2023-01-15": 2, "2023-01-16": 3}
    assert trend.statistical_significance == 1.8
    assert trend.tags == ["development", "local-government"]
    assert len(trend.entities) == 0
    assert len(trend.evidence) == 0

    # Test adding evidence
    evidence = TrendEvidenceItem(
        article_url="https://example.com/news/article1",
        published_at=datetime(2023, 1, 15, 14, 30, tzinfo=timezone.utc),
        evidence_text="Example evidence text",
    )
    trend.add_evidence(evidence)

    assert len(trend.evidence) == 1
    assert trend.evidence[0].article_url == "https://example.com/news/article1"
    assert trend.frequency_data["2023-01-15"] == 3  # Incremented from 2 to 3

    # Test adding entity
    entity = TrendEntity(
        text="Downtown Project",
        entity_type="ORG",
        frequency=5,
        relevance_score=0.9,
    )
    trend.add_entity(entity)

    assert len(trend.entities) == 1
    assert trend.entities[0].text == "Downtown Project"

    # Test updating existing entity
    entity2 = TrendEntity(
        text="Downtown Project",
        entity_type="ORG",
        frequency=3,
        relevance_score=0.95,
    )
    trend.add_entity(entity2)

    assert len(trend.entities) == 1  # Still only one entity
    assert trend.entities[0].frequency == 8  # 5 + 3
    assert trend.entities[0].relevance_score == 0.95  # Takes the higher score


def test_trend_analysis_config():
    """Test TrendAnalysisConfig defaults."""
    from src.local_newsifier.models.trend import TrendAnalysisConfig

    config = TrendAnalysisConfig()

    assert config.time_frame == TimeFrame.WEEK
    assert config.min_articles == 3
    assert config.min_confidence == 0.6
    assert config.entity_types == ["PERSON", "ORG", "GPE"]
    assert config.significance_threshold == 1.5
    assert config.topic_limit == 20
    assert config.lookback_periods == 4
