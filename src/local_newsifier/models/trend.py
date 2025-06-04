"""Models for trend detection and analysis in local news articles."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class TrendType(str, Enum):
    """Types of trends that can be detected in news articles."""

    EMERGING_TOPIC = "EMERGING_TOPIC"
    FREQUENCY_SPIKE = "FREQUENCY_SPIKE"
    NOVEL_ENTITY = "NOVEL_ENTITY"
    SUSTAINED_COVERAGE = "SUSTAINED_COVERAGE"
    ANOMALOUS_PATTERN = "ANOMALOUS_PATTERN"


class TrendStatus(str, Enum):
    """Status of a detected trend."""

    POTENTIAL = "POTENTIAL"
    CONFIRMED = "CONFIRMED"
    DECLINING = "DECLINING"
    EXPIRED = "EXPIRED"


class TopicFrequency(BaseModel):
    """Model representing frequency information for a topic over time."""

    topic: str
    frequencies: Dict[str, int]  # date string -> count
    entity_type: Optional[str] = None
    total_mentions: int = 0

    def add_occurrence(self, date: Union[datetime, str], count: int = 1) -> None:
        """
        Add an occurrence of the topic on a specific date.

        Args:
            date: The date of the occurrence
            count: Number of occurrences to add
        """
        date_str = date.isoformat().split("T")[0] if isinstance(date, datetime) else date
        if date_str in self.frequencies:
            self.frequencies[date_str] += count
        else:
            self.frequencies[date_str] = count
        self.total_mentions += count


class TrendEvidenceItem(BaseModel):
    """A single piece of evidence supporting a trend."""

    article_id: Optional[int] = None
    article_url: str
    article_title: Optional[str] = None
    published_at: datetime
    evidence_text: str
    relevance_score: float = 1.0


class TrendEntity(BaseModel):
    """An entity associated with a trend."""

    text: str
    entity_type: str
    frequency: int = 1
    relevance_score: float = 1.0


class TrendAnalysis(BaseModel):
    """Model representing a detected trend in news articles."""

    trend_id: UUID = Field(default_factory=uuid4)
    trend_type: TrendType
    name: str
    description: str
    status: TrendStatus = TrendStatus.POTENTIAL
    confidence_score: float
    start_date: datetime
    end_date: Optional[datetime] = None
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    entities: List[TrendEntity] = Field(default_factory=list)
    evidence: List[TrendEvidenceItem] = Field(default_factory=list)
    frequency_data: Dict[str, int] = Field(default_factory=dict)  # date -> count
    statistical_significance: Optional[float] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "trend_id": "123e4567-e89b-12d3-a456-426614174000",
                "trend_type": "EMERGING_TOPIC",
                "name": "Downtown Development Controversy",
                "description": "Increasing discussion of the new downtown development project",
                "status": "CONFIRMED",
                "confidence_score": 0.85,
                "start_date": "2023-01-15T00:00:00Z",
                "evidence": [
                    {
                        "article_url": "https://example.com/news/article1",
                        "published_at": "2023-01-15T14:30:00Z",
                        "evidence_text": "Controversy surrounds the downtown development...",
                    }
                ],
            }
        }
    )

    def add_evidence(self, item: TrendEvidenceItem) -> None:
        """
        Add a piece of evidence to the trend.

        Args:
            item: Evidence item to add
        """
        self.evidence.append(item)
        date_str = item.published_at.date().isoformat()

        # Update frequency data
        if date_str in self.frequency_data:
            self.frequency_data[date_str] += 1
        else:
            self.frequency_data[date_str] = 1

        # Update the last updated timestamp
        self.last_updated = datetime.now(timezone.utc)

    def add_entity(self, entity: TrendEntity) -> None:
        """
        Add or update an entity related to this trend.

        Args:
            entity: Entity to add or update
        """
        # Check if entity already exists
        for existing in self.entities:
            if existing.text == entity.text and existing.entity_type == entity.entity_type:
                existing.frequency += entity.frequency
                existing.relevance_score = max(existing.relevance_score, entity.relevance_score)
                return

        # Add new entity
        self.entities.append(entity)
        self.last_updated = datetime.now(timezone.utc)


class TimeFrame(str, Enum):
    """Time frames for trend analysis."""

    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"
    QUARTER = "QUARTER"
    YEAR = "YEAR"


class TrendAnalysisConfig(BaseModel):
    """Configuration for trend analysis."""

    time_frame: TimeFrame = TimeFrame.WEEK
    min_articles: int = 3
    min_confidence: float = 0.6
    entity_types: List[str] = Field(default_factory=lambda: ["PERSON", "ORG", "GPE"])
    significance_threshold: float = 1.5  # Z-score threshold
    topic_limit: int = 20  # Max number of topics to track
    include_historical: bool = True
    lookback_periods: int = 4  # How many periods to look back
