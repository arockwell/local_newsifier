import json
from datetime import datetime
from typing import Optional, Dict, Any
import boto3
from botocore.exceptions import ClientError

from ..models.state import NewsAnalysisState

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table_name = 'LocalNewsifierState'
table = dynamodb.Table(table_name)

def get_state_store() -> Dict[str, Any]:
    """Get the state store configuration."""
    return {
        "table_name": table_name,
        "table": table
    }

def save_state(state_store: Dict[str, Any], state: NewsAnalysisState) -> None:
    """
    Save the pipeline state to DynamoDB.
    
    Args:
        state_store: Configuration for the state store
        state: The state to save
    """
    try:
        state_store["table"].put_item(
            Item={
                'run_id': str(state.run_id),
                'timestamp': datetime.utcnow().isoformat(),
                'status': state.status.value,
                'target_url': state.target_url,
                'scraped_text': state.scraped_text,
                'analysis_results': state.analysis_results,
                'error_details': state.error_details.dict() if state.error_details else None,
                'run_logs': state.run_logs,
                'scraped_at': state.scraped_at.isoformat() if state.scraped_at else None,
                'analyzed_at': state.analyzed_at.isoformat() if state.analyzed_at else None,
                'saved_at': state.saved_at.isoformat() if state.saved_at else None,
                'save_path': state.save_path,
                'analysis_config': state.analysis_config,
                'retry_count': state.retry_count,
                'created_at': state.created_at.isoformat(),
                'last_updated': state.last_updated.isoformat()
            }
        )
    except ClientError as e:
        raise Exception(f"Failed to save state: {str(e)}")

def load_state(state_store: Dict[str, Any], run_id: str) -> Optional[NewsAnalysisState]:
    """
    Load a pipeline state from DynamoDB.
    
    Args:
        state_store: Configuration for the state store
        run_id: The run ID to load
        
    Returns:
        The loaded state or None if not found
    """
    try:
        response = state_store["table"].get_item(
            Key={
                'run_id': run_id
            }
        )
        
        if 'Item' not in response:
            return None
            
        item = response['Item']
        return NewsAnalysisState(
            run_id=item['run_id'],
            status=item['status'],
            target_url=item['target_url'],
            scraped_text=item['scraped_text'],
            analysis_results=item['analysis_results'],
            error_details=item['error_details'],
            run_logs=item['run_logs'],
            scraped_at=datetime.fromisoformat(item['scraped_at']) if item['scraped_at'] else None,
            analyzed_at=datetime.fromisoformat(item['analyzed_at']) if item['analyzed_at'] else None,
            saved_at=datetime.fromisoformat(item['saved_at']) if item['saved_at'] else None,
            save_path=item['save_path'],
            analysis_config=item['analysis_config'],
            retry_count=item['retry_count'],
            created_at=datetime.fromisoformat(item['created_at']),
            last_updated=datetime.fromisoformat(item['last_updated'])
        )
        
    except ClientError as e:
        raise Exception(f"Failed to load state: {str(e)}")

def list_states(state_store: Dict[str, Any], limit: int = 100) -> list:
    """
    List recent pipeline states.
    
    Args:
        state_store: Configuration for the state store
        limit: Maximum number of states to return
        
    Returns:
        List of state summaries
    """
    try:
        response = state_store["table"].scan(
            Limit=limit,
            ProjectionExpression='run_id, timestamp, status, target_url, created_at'
        )
        
        return response.get('Items', [])
        
    except ClientError as e:
        raise Exception(f"Failed to list states: {str(e)}") 