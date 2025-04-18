"""Tool for analyzing topic frequencies in news articles."""

import math
from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
from sqlmodel import Session

from local_newsifier.models.database.analysis_result import AnalysisResult
from local_newsifier.models.database.article import Article
from local_newsifier.models.trend import TimeFrame, TopicFrequency
from local_newsifier.tools.historical_aggregator import HistoricalDataAggregator
from local_newsifier.database.engine import with_session


class TopicFrequencyAnalyzer:
    """Tool for analyzing frequency patterns in news article topics."""

    def __init__(self, data_aggregator: Optional[HistoricalDataAggregator] = None):
        """
        Initialize the topic frequency analyzer.

        Args:
            data_aggregator: Optional HistoricalDataAggregator instance.
                             If not provided, a new one will be created.
        """
        self.data_aggregator = data_aggregator if data_aggregator is not None else HistoricalDataAggregator()

    def calculate_statistical_significance(
        self,
        current: TopicFrequency,
        baseline: Optional[TopicFrequency],
        threshold: float = 1.5,
    ) -> Tuple[float, bool]:
        """
        Calculate the statistical significance of frequency changes.

        Args:
            current: Current period frequency data
            baseline: Baseline period frequency data
            threshold: Z-score threshold for significance

        Returns:
            Tuple of (z_score, is_significant)
        """
        # If no baseline or baseline has no mentions, treat as significant new topic
        if not baseline or baseline.total_mentions == 0:
            # New topics get a default z-score of 2.0 if they have enough mentions
            return 2.0, current.total_mentions >= 2

        # Calculate frequency ratio
        current_rate = current.total_mentions / len(current.frequencies)
        baseline_rate = baseline.total_mentions / len(baseline.frequencies)

        # Need some variance for meaningful z-score
        # If baseline has very few mentions or days, use a simplified approach
        if baseline.total_mentions < 3 or len(baseline.frequencies) < 3:
            # Simple fold change
            if current_rate > baseline_rate * 1.5:
                return 2.0, True
            return 0.0, False

        # Calculate variance of baseline (if enough data points)
        baseline_counts = list(baseline.frequencies.values())
        if len(baseline_counts) >= 3:
            baseline_std = np.std(baseline_counts)
            if baseline_std > 0:
                z_score = (current_rate - baseline_rate) / baseline_std
                return z_score, z_score >= threshold

        # Fallback if we can't calculate a proper z-score
        if current_rate > baseline_rate * 1.5:
            return 1.5, True

        return 0.0, False

    @with_session
    def identify_significant_changes(
        self,
        entity_types: List[str],
        time_frame: TimeFrame,
        significance_threshold: float = 1.5,
        min_mentions: int = 2,
        *,
        session: Optional[Session] = None
    ) -> Dict[str, Dict]:
        """
        Identify statistically significant changes in topic frequencies.

        Args:
            entity_types: List of entity types to analyze
            time_frame: Time frame for analysis
            significance_threshold: Z-score threshold for significance
            min_mentions: Minimum mentions required for consideration

        Returns:
            Dictionary of significant topics with their metrics
        """
        # Get current and baseline frequencies
        current_freqs, baseline_freqs = self.data_aggregator.get_baseline_frequencies(
            entity_types, time_frame, session=session
        )

        significant_changes = {}

        # Analyze each topic
        for key, current in current_freqs.items():
            # Skip topics with too few mentions
            if current.total_mentions < min_mentions:
                continue

            # Get corresponding baseline frequency
            baseline = baseline_freqs.get(key)

            # Calculate significance
            z_score, is_significant = self.calculate_statistical_significance(
                current, baseline, significance_threshold
            )

            if is_significant:
                # Store significant topic with metrics
                significant_changes[key] = {
                    "topic": current.topic,
                    "entity_type": current.entity_type,
                    "current_frequency": current.total_mentions,
                    "baseline_frequency": baseline.total_mentions if baseline else 0,
                    "change_percent": (
                        (
                            (
                                current.total_mentions
                                / max(1, baseline.total_mentions if baseline else 0)
                            )
                            - 1
                        )
                        * 100
                    ),
                    "z_score": z_score,
                    "is_new": baseline is None or baseline.total_mentions == 0,
                }

        return significant_changes

    def analyze_frequency_patterns(
        self,
        topic_frequencies: Dict[str, TopicFrequency],
        min_data_points: int = 3,
    ) -> Dict[str, Dict]:
        """
        Analyze patterns in topic frequencies over time.

        Args:
            topic_frequencies: Dictionary of topic frequencies
            min_data_points: Minimum data points required for pattern analysis

        Returns:
            Dictionary of patterns detected for each topic
        """
        patterns = {}

        for key, freq in topic_frequencies.items():
            # Need enough data points for pattern analysis
            if len(freq.frequencies) < min_data_points:
                continue

            # Sort frequency data by date
            sorted_dates = sorted(freq.frequencies.keys())
            sorted_counts = [freq.frequencies[date] for date in sorted_dates]

            # Pattern detection
            pattern_info = {
                "topic": freq.topic,
                "entity_type": freq.entity_type,
                "total_mentions": freq.total_mentions,
                "peak_date": max(freq.frequencies.items(), key=lambda x: x[1])[0],
                "peak_value": max(freq.frequencies.values()),
                "is_rising": False,
                "is_falling": False,
                "is_spiky": False,
                "is_consistent": False,
            }

            # Simple trend detection
            if len(sorted_counts) >= 3:
                # Linear regression for trend
                x = np.arange(len(sorted_counts))
                slope, _ = np.polyfit(x, sorted_counts, 1)

                pattern_info["slope"] = slope
                pattern_info["is_rising"] = slope > 0.5
                pattern_info["is_falling"] = slope < -0.5

                # Variance analysis
                mean = np.mean(sorted_counts)
                std = np.std(sorted_counts)
                coefficient_of_variation = std / max(1, mean)

                pattern_info["coefficient_of_variation"] = coefficient_of_variation
                pattern_info["is_spiky"] = coefficient_of_variation > 1.0
                pattern_info["is_consistent"] = coefficient_of_variation < 0.5

            patterns[key] = pattern_info

        return patterns

    def find_related_topics(
        self, topic: str, entity_type: str, all_frequencies: Dict[str, TopicFrequency]
    ) -> List[Dict]:
        """
        Find topics that frequently appear with the given topic.

        Args:
            topic: The main topic
            entity_type: Entity type of the main topic
            all_frequencies: Dictionary of all topic frequencies

        Returns:
            List of related topics with correlation scores
        """
        main_key = f"{topic}:{entity_type}"
        if main_key not in all_frequencies:
            return []

        main_topic = all_frequencies[main_key]
        main_dates = set(main_topic.frequencies.keys())

        related = []

        for key, other_topic in all_frequencies.items():
            if key == main_key:
                continue

            other_dates = set(other_topic.frequencies.keys())

            # Calculate overlap
            date_overlap = main_dates.intersection(other_dates)
            if not date_overlap:
                continue

            # Calculate co-occurrence rate
            co_occurrence_rate = len(date_overlap) / len(main_dates)
            if co_occurrence_rate >= 0.3:  # At least 30% co-occurrence
                related.append(
                    {
                        "topic": other_topic.topic,
                        "entity_type": other_topic.entity_type,
                        "co_occurrence_rate": co_occurrence_rate,
                        "co_occurrence_count": len(date_overlap),
                    }
                )

        # Sort by co-occurrence rate
        related.sort(key=lambda x: x["co_occurrence_rate"], reverse=True)
        return related
