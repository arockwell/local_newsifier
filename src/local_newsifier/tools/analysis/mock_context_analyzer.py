"""Mock Context Analyzer for testing."""

from typing import Dict, Any


class MockContextAnalyzer:
    """Mock context analyzer for testing purposes."""
    
    def analyze_context(self, context: str) -> Dict[str, Any]:
        """
        Mock method to analyze context.
        
        Args:
            context: Text context to analyze
            
        Returns:
            Analysis results
        """
        # Return dummy analysis results for testing
        return {
            "sentiment": {
                "score": 0.65,
                "label": "positive"
            },
            "framing": {
                "category": "informative",
                "confidence": 0.8
            },
            "keywords": ["test", "mock", "context"]
        }
