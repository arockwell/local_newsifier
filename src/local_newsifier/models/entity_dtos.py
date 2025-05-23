"""DTOs for entity service operations."""

from typing import List, Optional

from pydantic import BaseModel, Field

from .dto_base import BaseListResultDTO, BaseOperationResultDTO, ProcessingStatus


class ProcessedEntityDTO(BaseModel):
    """DTO for individual processed entity results."""
    
    original_text: str
    canonical_name: str
    canonical_id: int
    entity_type: str
    context: str
    sentiment_score: float = Field(ge=-1.0, le=1.0)
    framing_category: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    
    # Additional metadata that was missing from original dict
    position_in_text: Optional[int] = None
    sentence_context: Optional[str] = None
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "original_text": "Mayor Johnson",
                    "canonical_name": "Mayor Sarah Johnson",
                    "canonical_id": 123,
                    "entity_type": "PERSON",
                    "context": "Mayor Johnson announced the new downtown development project",
                    "sentiment_score": 0.3,
                    "framing_category": "neutral",
                    "confidence_score": 0.95,
                    "position_in_text": 45,
                    "sentence_context": "In a press conference today, Mayor Johnson announced..."
                }
            ]
        }
    }


class EntityProcessingResultDTO(BaseModel):
    """DTO for single article entity processing results."""
    
    article_id: int
    article_title: str
    article_url: str
    entity_count: int = Field(ge=0)
    entities: List[ProcessedEntityDTO] = Field(default_factory=list)
    processing_status: ProcessingStatus
    processing_duration_ms: Optional[int] = None
    error_details: Optional[str] = None
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "article_id": 123,
                    "article_title": "City Council Approves New Budget",
                    "article_url": "https://example.com/news/budget-approval",
                    "entity_count": 5,
                    "entities": [
                        {
                            "original_text": "City Council",
                            "canonical_name": "Gainesville City Council",
                            "canonical_id": 456,
                            "entity_type": "ORG",
                            "context": "City Council approved the budget",
                            "sentiment_score": 0.1,
                            "framing_category": "neutral",
                            "confidence_score": 0.9
                        }
                    ],
                    "processing_status": "completed",
                    "processing_duration_ms": 1200
                }
            ]
        }
    }


class EntityBatchProcessingResultDTO(BaseListResultDTO[EntityProcessingResultDTO]):
    """
    Standardized response for batch entity processing operations.
    
    Replaces the complex state tracking and ad-hoc result structures
    from EntityService batch operations with paginated, validated results.
    """
    
    # Batch operation summary
    total_articles: int = Field(ge=0)
    successful_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)
    skipped_count: int = Field(ge=0, default=0)
    
    # Processing metrics
    total_entities_extracted: int = Field(ge=0, default=0)
    average_entities_per_article: float = Field(ge=0.0, default=0.0)
    total_processing_duration_ms: Optional[int] = None
    
    # Batch configuration
    batch_id: Optional[str] = None
    processing_algorithm: str = "default"
    confidence_threshold: float = Field(ge=0.0, le=1.0, default=0.6)
    
    def __init__(self, **data):
        super().__init__(**data)
        # Auto-calculate metrics
        if self.items:
            self.total_entities_extracted = sum(item.entity_count for item in self.items)
            if self.total_articles > 0:
                self.average_entities_per_article = self.total_entities_extracted / self.total_articles
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "items": [
                        {
                            "article_id": 123,
                            "article_title": "City Council Approves Budget",
                            "article_url": "https://example.com/news/1",
                            "entity_count": 5,
                            "entities": [],
                            "processing_status": "completed"
                        }
                    ],
                    "total": 100,
                    "page": 1,
                    "size": 50,
                    "total_articles": 100,
                    "successful_count": 95,
                    "failed_count": 5,
                    "total_entities_extracted": 487,
                    "average_entities_per_article": 4.87,
                    "batch_id": "batch-2023-01-01-123",
                    "processing_algorithm": "spacy_nlp_v3",
                    "confidence_threshold": 0.7
                }
            ]
        }
    }


class EntityResolutionResultDTO(BaseModel):
    """DTO for entity resolution operation results."""
    
    original_entity_text: str
    resolved_canonical_id: Optional[int] = None
    resolved_canonical_name: Optional[str] = None
    resolution_confidence: float = Field(ge=0.0, le=1.0)
    resolution_method: str = "default"
    
    # Resolution metadata
    similar_entities: List[str] = Field(default_factory=list)
    disambiguation_factors: List[str] = Field(default_factory=list)
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "original_entity_text": "Mayor Johnson",
                    "resolved_canonical_id": 123,
                    "resolved_canonical_name": "Mayor Sarah Johnson",
                    "resolution_confidence": 0.95,
                    "resolution_method": "fuzzy_matching",
                    "similar_entities": ["Sarah Johnson", "S. Johnson"],
                    "disambiguation_factors": ["title_match", "context_similarity"]
                }
            ]
        }
    }


class EntityTrackingConfigDTO(BaseModel):
    """DTO for entity tracking configuration parameters."""
    
    confidence_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    max_entities_per_article: int = Field(default=50, ge=1, le=500)
    enable_sentiment_analysis: bool = True
    enable_entity_resolution: bool = True
    entity_types_to_track: List[str] = Field(default_factory=lambda: ["PERSON", "ORG", "GPE"])
    
    # Advanced options
    use_canonical_entities: bool = True
    similarity_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    context_window_size: int = Field(default=100, ge=10, le=500)
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "confidence_threshold": 0.7,
                    "max_entities_per_article": 30,
                    "enable_sentiment_analysis": True,
                    "enable_entity_resolution": True,
                    "entity_types_to_track": ["PERSON", "ORG", "GPE", "EVENT"],
                    "use_canonical_entities": True,
                    "similarity_threshold": 0.85,
                    "context_window_size": 150
                }
            ]
        }
    }