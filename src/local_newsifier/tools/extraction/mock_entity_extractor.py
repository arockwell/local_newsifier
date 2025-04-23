"""Mock Entity Extractor for testing."""

from typing import Dict, List, Any


class MockEntityExtractor:
    """Mock entity extractor for testing purposes."""
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Mock method to extract entities from text.
        
        Args:
            text: Text to extract entities from
            
        Returns:
            List of extracted entities
        """
        # Just return a dummy entity for testing
        return [
            {
                "text": "Test Entity",
                "type": "PERSON",
                "confidence": 0.95,
                "context": "This is a test entity in a mock context."
            }
        ]
