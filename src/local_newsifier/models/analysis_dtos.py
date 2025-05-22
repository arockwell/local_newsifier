"""DTOs for analysis service operations."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .dto_base import BaseOperationResultDTO, MetadataDTO


class KeywordCountDTO(BaseModel):
    """DTO for keyword frequency data."""
    
    keyword: str
    count: int
    percentage: float = Field(ge=0.0, le=100.0)
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "keyword": "downtown",
                    "count": 15,
                    "percentage": 12.5
                }
            ]
        }
    }


class TrendingTermDTO(BaseModel):
    """DTO for trending term analysis."""
    
    term: str
    total_mentions: int = Field(ge=0)
    growth_rate: float
    significance_score: float = Field(ge=0.0, le=1.0)
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "term": "city council",
                    "total_mentions": 25,
                    "growth_rate": 0.45,
                    "significance_score": 0.8,
                    "first_seen": "2023-01-01T00:00:00Z",
                    "last_seen": "2023-01-07T23:59:59Z"
                }
            ]
        }
    }


class AnalysisMetadataDTO(MetadataDTO):
    """Extended metadata for analysis operations."""
    
    articles_analyzed: int = Field(ge=0)
    time_period_start: Optional[datetime] = None
    time_period_end: Optional[datetime] = None
    analysis_algorithm: str = "default"
    confidence_threshold: float = Field(ge=0.0, le=1.0, default=0.6)
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "articles_analyzed": 150,
                    "time_period_start": "2023-01-01T00:00:00Z",
                    "time_period_end": "2023-01-07T23:59:59Z",
                    "analysis_algorithm": "spacy_nlp_v3",
                    "confidence_threshold": 0.7,
                    "processing_duration_ms": 2500
                }
            ]
        }
    }


class HeadlineTrendResponseDTO(BaseOperationResultDTO):
    """
    Standardized response for headline trend analysis operations.
    
    Replaces the ad-hoc dictionary structure returned by 
    AnalysisService.analyze_headline_trends() with a validated, 
    consistent format.
    """
    
    trending_terms: List[TrendingTermDTO] = Field(default_factory=list)
    overall_top_terms: List[KeywordCountDTO] = Field(default_factory=list)
    period_counts: Dict[str, int] = Field(default_factory=dict)
    analysis_metadata: AnalysisMetadataDTO
    
    # Pagination support for large result sets
    trending_terms_total: int = 0
    top_terms_total: int = 0
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "status": "completed",
                    "trending_terms": [
                        {
                            "term": "city council",
                            "total_mentions": 25,
                            "growth_rate": 0.45,
                            "significance_score": 0.8
                        }
                    ],
                    "overall_top_terms": [
                        {
                            "keyword": "downtown",
                            "count": 15,
                            "percentage": 12.5
                        }
                    ],
                    "period_counts": {
                        "2023-01-01": 10,
                        "2023-01-02": 15,
                        "2023-01-03": 12
                    },
                    "analysis_metadata": {
                        "articles_analyzed": 150,
                        "processing_duration_ms": 2500,
                        "analysis_algorithm": "spacy_nlp_v3"
                    }
                }
            ]
        }
    }


class EntityAnalysisResultDTO(BaseModel):
    """DTO for individual entity analysis results."""
    
    entity_text: str
    entity_type: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    sentiment_score: Optional[float] = Field(None, ge=-1.0, le=1.0)
    context_snippet: Optional[str] = None
    canonical_id: Optional[int] = None
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "entity_text": "Mayor Johnson",
                    "entity_type": "PERSON",
                    "confidence_score": 0.95,
                    "sentiment_score": 0.2,
                    "context_snippet": "Mayor Johnson announced the new initiative",
                    "canonical_id": 123
                }
            ]
        }
    }


class TrendAnalysisConfigDTO(BaseModel):
    """DTO for trend analysis configuration parameters."""
    
    time_interval: str = Field(default="day", pattern=r"^(hour|day|week|month)$")
    min_articles: int = Field(default=3, ge=1)
    min_confidence: float = Field(default=0.6, ge=0.0, le=1.0)
    max_results: int = Field(default=50, ge=1, le=1000)
    include_sentiment: bool = True
    entity_types: List[str] = Field(default_factory=lambda: ["PERSON", "ORG", "GPE"])
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "time_interval": "day",
                    "min_articles": 5,
                    "min_confidence": 0.7,
                    "max_results": 20,
                    "include_sentiment": True,
                    "entity_types": ["PERSON", "ORG", "GPE", "EVENT"]
                }
            ]
        }
    }