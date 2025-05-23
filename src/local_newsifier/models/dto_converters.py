"""Utility functions for converting data to DTOs."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .analysis_dtos import (
    AnalysisMetadataDTO,
    HeadlineTrendResponseDTO,
    KeywordCountDTO,
    TrendingTermDTO,
)
from .dto_base import ErrorResponseDTO, ProcessingStatus


def convert_to_trending_terms(raw_terms: List[Dict[str, Any]]) -> List[TrendingTermDTO]:
    """
    Convert raw trending terms data to TrendingTermDTO objects.
    
    Args:
        raw_terms: List of dictionaries containing trending term data
        
    Returns:
        List of TrendingTermDTO objects
    """
    trending_terms = []
    
    for term_data in raw_terms:
        try:
            trending_term = TrendingTermDTO(
                term=term_data.get("term", ""),
                total_mentions=term_data.get("total_mentions", 0),
                growth_rate=term_data.get("growth_rate", 0.0),
                significance_score=min(1.0, max(0.0, term_data.get("significance_score", 0.5))),
                first_seen=term_data.get("first_seen"),
                last_seen=term_data.get("last_seen")
            )
            trending_terms.append(trending_term)
        except Exception:
            # Skip invalid term data rather than failing entire conversion
            continue
    
    return trending_terms


def convert_to_keyword_counts(raw_terms: List[Tuple[str, int]], total_terms: int = None) -> List[KeywordCountDTO]:
    """
    Convert raw keyword count data to KeywordCountDTO objects.
    
    Args:
        raw_terms: List of tuples containing (keyword, count) data
        total_terms: Total number of terms for percentage calculation
        
    Returns:
        List of KeywordCountDTO objects
    """
    if total_terms is None:
        total_terms = sum(count for _, count in raw_terms) if raw_terms else 1
    
    keyword_counts = []
    
    for keyword, count in raw_terms:
        try:
            percentage = (count / total_terms * 100) if total_terms > 0 else 0.0
            
            keyword_count = KeywordCountDTO(
                keyword=keyword,
                count=count,
                percentage=min(100.0, max(0.0, percentage))
            )
            keyword_counts.append(keyword_count)
        except Exception:
            # Skip invalid keyword data rather than failing entire conversion
            continue
    
    return keyword_counts


def convert_analysis_result_to_dto(
    result: Dict[str, Any],
    processing_duration_ms: Optional[int] = None,
    articles_analyzed: Optional[int] = None
) -> HeadlineTrendResponseDTO:
    """
    Convert legacy analysis result dictionary to HeadlineTrendResponseDTO.
    
    Args:
        result: Legacy result dictionary from analyze_headline_trends
        processing_duration_ms: Processing duration in milliseconds
        articles_analyzed: Number of articles analyzed
        
    Returns:
        HeadlineTrendResponseDTO object
    """
    # Handle error cases
    if "error" in result:
        return HeadlineTrendResponseDTO(
            success=False,
            status=ProcessingStatus.FAILED,
            error_message=result["error"],
            trending_terms=[],
            overall_top_terms=[],
            period_counts={},
            analysis_metadata=AnalysisMetadataDTO(
                articles_analyzed=0,
                processing_duration_ms=processing_duration_ms
            )
        )
    
    # Convert trending terms
    trending_terms = convert_to_trending_terms(result.get("trending_terms", []))
    
    # Convert overall top terms
    raw_top_terms = result.get("overall_top_terms", [])
    overall_top_terms = convert_to_keyword_counts(raw_top_terms)
    
    # Get period counts
    period_counts = result.get("period_counts", {})
    
    # Calculate total articles if not provided
    if articles_analyzed is None:
        articles_analyzed = sum(period_counts.values()) if period_counts else 0
    
    # Create metadata
    analysis_metadata = AnalysisMetadataDTO(
        articles_analyzed=articles_analyzed,
        processing_duration_ms=processing_duration_ms,
        source="analysis_service",
        additional_info={
            "raw_data_periods": len(result.get("raw_data", {})),
            "has_trending_terms": len(trending_terms) > 0,
            "has_top_terms": len(overall_top_terms) > 0
        }
    )
    
    return HeadlineTrendResponseDTO(
        success=True,
        status=ProcessingStatus.COMPLETED,
        trending_terms=trending_terms,
        overall_top_terms=overall_top_terms,
        period_counts=period_counts,
        analysis_metadata=analysis_metadata,
        trending_terms_total=len(trending_terms),
        top_terms_total=len(overall_top_terms)
    )


def create_error_response_dto(
    error_code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> ErrorResponseDTO:
    """
    Create a standardized error response DTO.
    
    Args:
        error_code: Error code from ErrorResponseDTO constants
        message: Human-readable error message
        details: Optional error details
        request_id: Optional request ID for tracking
        
    Returns:
        ErrorResponseDTO object
    """
    return ErrorResponseDTO(
        error_code=error_code,
        message=message,
        details=details,
        request_id=request_id,
        timestamp=datetime.now(timezone.utc)
    )


def extract_dto_metadata(dto_result: HeadlineTrendResponseDTO) -> Dict[str, Any]:
    """
    Extract metadata from a DTO for logging or debugging purposes.
    
    Args:
        dto_result: HeadlineTrendResponseDTO object
        
    Returns:
        Dictionary containing key metadata
    """
    return {
        "success": dto_result.success,
        "status": dto_result.status,
        "trending_terms_count": len(dto_result.trending_terms),
        "top_terms_count": len(dto_result.overall_top_terms),
        "periods_analyzed": len(dto_result.period_counts),
        "total_articles": dto_result.analysis_metadata.articles_analyzed,
        "processing_duration_ms": dto_result.analysis_metadata.processing_duration_ms,
        "operation_id": dto_result.operation_id,
        "timestamp": dto_result.timestamp.isoformat()
    }