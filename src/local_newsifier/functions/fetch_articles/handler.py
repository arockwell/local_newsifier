import json
import logging
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from local_newsifier.flows.news_pipeline import NewsPipelineFlow
from local_newsifier.models.state import AnalysisStatus
from local_newsifier.shared.state import get_state_store, save_state

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for fetching and processing new articles.
    
    Expected event format:
    {
        "sources": [
            {
                "url": "https://example.com/news",
                "type": "rss" | "web"
            }
        ]
    }
    """
    try:
        # Initialize pipeline
        pipeline = NewsPipelineFlow(output_dir="/tmp/output")
        
        # Get state store
        state_store = get_state_store()
        
        # Process each source
        results = []
        for source in event.get("sources", []):
            try:
                # Start pipeline for this source
                state = pipeline.start_pipeline(url=source["url"])
                
                # Save state
                save_state(state_store, state)
                
                results.append({
                    "source": source["url"],
                    "status": state.status.value,
                    "run_id": state.run_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error processing source {source['url']}: {str(e)}")
                results.append({
                    "source": source["url"],
                    "status": "ERROR",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Article fetch completed",
                "results": results
            })
        }
        
    except Exception as e:
        logger.error(f"Lambda execution failed: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Internal server error",
                "error": str(e)
            })
        } 