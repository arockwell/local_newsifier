"""CRUD operations for AnalysisResult model."""

from typing import Dict, List, Optional, Any

from sqlmodel import Session, select

from local_newsifier.models.analysis_result import AnalysisResult


def create_analysis_result(session: Session, result_data: Dict[str, Any]) -> AnalysisResult:
    """Create a new analysis result in the database.
    
    Args:
        session: Database session
        result_data: Analysis result data dictionary
        
    Returns:
        Created analysis result
    """
    db_result = AnalysisResult(**result_data)
    session.add(db_result)
    session.commit()
    session.refresh(db_result)
    return db_result


def get_analysis_result(session: Session, result_id: int) -> Optional[AnalysisResult]:
    """Get an analysis result by ID.
    
    Args:
        session: Database session
        result_id: ID of the analysis result to get
        
    Returns:
        Analysis result if found, None otherwise
    """
    return session.get(AnalysisResult, result_id)


def get_results_by_type(session: Session, analysis_type: str) -> List[AnalysisResult]:
    """Get all analysis results of a specific type.
    
    Args:
        session: Database session
        analysis_type: Type of analysis results to get
        
    Returns:
        List of analysis results of the specified type
    """
    statement = select(AnalysisResult).where(AnalysisResult.analysis_type == analysis_type)
    return session.exec(statement).all()


def get_results_by_article_and_type(
    session: Session, article_id: int, analysis_type: str
) -> List[AnalysisResult]:
    """Get analysis results for an article of a specific type.
    
    Args:
        session: Database session
        article_id: ID of the article
        analysis_type: Type of analysis results to get
        
    Returns:
        List of analysis results for the article of the specified type
    """
    statement = select(AnalysisResult).where(
        AnalysisResult.article_id == article_id,
        AnalysisResult.analysis_type == analysis_type
    )
    return session.exec(statement).all()


def delete_analysis_result(session: Session, result_id: int) -> bool:
    """Delete an analysis result from the database.
    
    Args:
        session: Database session
        result_id: ID of the analysis result to delete
        
    Returns:
        True if analysis result was deleted, False otherwise
    """
    result = session.get(AnalysisResult, result_id)
    if result:
        session.delete(result)
        session.commit()
        return True
    return False