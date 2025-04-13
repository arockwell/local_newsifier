"""Tests for the TopicFrequencyAnalyzer tool."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
import numpy as np

from src.local_newsifier.models.trend import TimeFrame, TopicFrequency
from src.local_newsifier.tools.topic_analyzer import TopicFrequencyAnalyzer


@pytest.fixture
def mock_data_aggregator():
    """Fixture for a mocked HistoricalDataAggregator."""
    return MagicMock()

@pytest.fixture(autouse=True)
def mock_dependencies():
    """Fixture to mock dependencies."""
    with patch("src.local_newsifier.tools.topic_analyzer.HistoricalDataAggregator") as mock_agg:
        mock_agg.return_value = MagicMock()
        yield mock_agg


@pytest.fixture
def sample_topic_frequencies():
    """Fixture providing sample topic frequency data."""
    return {
        "Mayor Johnson:PERSON": TopicFrequency(
            topic="Mayor Johnson",
            entity_type="PERSON",
            frequencies={"2023-01-01": 1, "2023-01-02": 2, "2023-01-03": 3},
            total_mentions=6,
        ),
        "City Council:ORG": TopicFrequency(
            topic="City Council",
            entity_type="ORG",
            frequencies={"2023-01-01": 2, "2023-01-03": 2, "2023-01-04": 1},
            total_mentions=5,
        ),
        "Downtown Project:ORG": TopicFrequency(
            topic="Downtown Project",
            entity_type="ORG",
            frequencies={"2023-01-02": 1, "2023-01-03": 3, "2023-01-04": 2},
            total_mentions=6,
        ),
        "Gainesville:GPE": TopicFrequency(
            topic="Gainesville",
            entity_type="GPE",
            frequencies={"2023-01-01": 1, "2023-01-02": 1, "2023-01-03": 1, "2023-01-04": 1},
            total_mentions=4,
        ),
    }


def test_init(mock_data_aggregator):
    """Test TopicFrequencyAnalyzer initialization."""
    with patch("src.local_newsifier.tools.topic_analyzer.HistoricalDataAggregator") as mock_agg_cls:
        mock_agg_instance = MagicMock()
        mock_agg_cls.return_value = mock_agg_instance
        
        # Test with default initialization
        analyzer = TopicFrequencyAnalyzer()
        assert analyzer.data_aggregator == mock_agg_instance
        
        # Test with provided data_aggregator
        analyzer = TopicFrequencyAnalyzer(data_aggregator=mock_data_aggregator)
        assert analyzer.data_aggregator == mock_data_aggregator


def test_calculate_statistical_significance():
    """Test calculation of statistical significance."""
    analyzer = TopicFrequencyAnalyzer()
    
    # Test with no baseline (new topic)
    current = TopicFrequency(
        topic="New Topic",
        entity_type="ORG",
        frequencies={"2023-01-01": 2, "2023-01-02": 3},
        total_mentions=5,
    )
    z_score, is_significant = analyzer.calculate_statistical_significance(current, None)
    assert z_score == 2.0
    assert is_significant == True
    
    # Test with baseline but not enough mentions
    baseline = TopicFrequency(
        topic="New Topic",
        entity_type="ORG",
        frequencies={"2022-12-30": 1},
        total_mentions=1,
    )
    z_score, is_significant = analyzer.calculate_statistical_significance(current, baseline)
    assert z_score == 2.0
    assert is_significant == True
    
    # Test with baseline and sufficient data
    baseline = TopicFrequency(
        topic="Topic",
        entity_type="ORG",
        frequencies={"2022-12-28": 1, "2022-12-29": 2, "2022-12-30": 1},
        total_mentions=4,
    )
    
    # Mock numpy std to return a predictable value
    with patch.object(np, 'std', return_value=0.5):
        z_score, is_significant = analyzer.calculate_statistical_significance(current, baseline)
        assert z_score > 0
        
    # Test with zero standard deviation (all values the same)
    with patch.object(np, 'std', return_value=0):
        z_score, is_significant = analyzer.calculate_statistical_significance(current, baseline)
        assert is_significant == (current.total_mentions / len(current.frequencies) > 
                                baseline.total_mentions / len(baseline.frequencies) * 1.5)


@patch("src.local_newsifier.tools.topic_analyzer.TopicFrequencyAnalyzer.calculate_statistical_significance")
def test_identify_significant_changes(mock_calc_significance, mock_data_aggregator, sample_topic_frequencies):
    """Test identification of significant changes in topics."""
    # Setup
    current_freqs = sample_topic_frequencies
    baseline_freqs = {
        "Mayor Johnson:PERSON": TopicFrequency(
            topic="Mayor Johnson",
            entity_type="PERSON",
            frequencies={"2022-12-25": 1, "2022-12-26": 1},
            total_mentions=2,
        ),
        "City Council:ORG": TopicFrequency(
            topic="City Council",
            entity_type="ORG",
            frequencies={"2022-12-25": 2, "2022-12-26": 2, "2022-12-27": 2},
            total_mentions=6,
        ),
    }
    
    mock_data_aggregator.get_baseline_frequencies.return_value = (current_freqs, baseline_freqs)
    
    # Set up different significance results
    def side_effect(current, baseline, threshold=1.5):
        if current.topic == "Mayor Johnson":
            return 2.5, True
        elif current.topic == "Downtown Project":
            return 3.0, True
        else:
            return 0.5, False
    
    mock_calc_significance.side_effect = side_effect
    
    analyzer = TopicFrequencyAnalyzer(data_aggregator=mock_data_aggregator)
    
    # Test identification of significant changes
    result = analyzer.identify_significant_changes(
        entity_types=["PERSON", "ORG"],
        time_frame=TimeFrame.WEEK,
        significance_threshold=1.5,
        min_mentions=2,
    )
    
    assert "Mayor Johnson:PERSON" in result
    assert "Downtown Project:ORG" in result
    assert "City Council:ORG" not in result
    
    # Check that the results have the expected format
    assert result["Mayor Johnson:PERSON"]["topic"] == "Mayor Johnson"
    assert result["Mayor Johnson:PERSON"]["entity_type"] == "PERSON"
    assert "z_score" in result["Mayor Johnson:PERSON"]
    assert "change_percent" in result["Mayor Johnson:PERSON"]
    assert result["Mayor Johnson:PERSON"]["is_new"] is False


def test_analyze_frequency_patterns(sample_topic_frequencies):
    """Test analysis of frequency patterns over time."""
    analyzer = TopicFrequencyAnalyzer()
    
    # Test pattern detection
    result = analyzer.analyze_frequency_patterns(sample_topic_frequencies)
    
    # Check each topic
    assert "Mayor Johnson:PERSON" in result
    assert "City Council:ORG" in result
    assert "Downtown Project:ORG" in result
    assert "Gainesville:GPE" in result
    
    # Check that the results have the expected format
    for key, pattern in result.items():
        assert "topic" in pattern
        assert "entity_type" in pattern
        assert "total_mentions" in pattern
        assert "peak_date" in pattern
        assert "peak_value" in pattern
        
        # Check that trend indicators are present
        if len(sample_topic_frequencies[key].frequencies) >= 3:
            assert "slope" in pattern
            assert "is_rising" in pattern
            assert "is_falling" in pattern
            assert "coefficient_of_variation" in pattern
            assert "is_spiky" in pattern
            assert "is_consistent" in pattern


def test_find_related_topics(sample_topic_frequencies):
    """Test finding related topics based on co-occurrence."""
    analyzer = TopicFrequencyAnalyzer()
    
    # Test finding related topics for "Mayor Johnson"
    related = analyzer.find_related_topics(
        "Mayor Johnson", "PERSON", sample_topic_frequencies
    )
    
    # Check format of results
    for item in related:
        assert "topic" in item
        assert "entity_type" in item
        assert "co_occurrence_rate" in item
        assert "co_occurrence_count" in item
        
    # Test for a topic not in the data
    related = analyzer.find_related_topics(
        "Not In Data", "PERSON", sample_topic_frequencies
    )
    assert related == []