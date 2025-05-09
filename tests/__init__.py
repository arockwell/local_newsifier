"""
Test package initialization.

This file contains initialization code for tests, including global patches
that need to be applied before any tests are run.
"""

from unittest.mock import MagicMock, patch

# Early patch for spaCy to avoid loading models in all tests
class MockSpacyDoc:
    """Mock spaCy Doc class."""
    def __init__(self, text="Test content"):
        self.text = text
        self.ents = []
        self._sentences = [MockSpacySent("Test sentence.")]
    
    @property
    def sents(self):
        return self._sentences
    
    def char_span(self, start_char, end_char, **kwargs):
        """Mock character span lookup."""
        mock_span = MagicMock()
        mock_span.start = 0
        mock_span.end = 10
        return mock_span

class MockSpacySent:
    """Mock spaCy Sent (sentence) class."""
    def __init__(self, text="Test sentence."):
        self.text = text
        self.start_char = 0
        self.end_char = len(text)
        self.start = 0
        self.end = len(text.split())

class MockSpacyLanguage:
    """Mock spaCy Language class."""
    def __init__(self):
        self.vocab = {}
        self.pipeline = []
    
    def __call__(self, text):
        """Process text and return a Doc object."""
        doc = MockSpacyDoc(text)
        
        # Create some mock entities
        mock_ent1 = MagicMock()
        mock_ent1.text = "Entity1"
        mock_ent1.label_ = "PERSON"
        mock_ent1.start_char = 0
        mock_ent1.end_char = 7
        mock_ent1.sent = doc.sents[0]
        
        mock_ent2 = MagicMock()
        mock_ent2.text = "Entity2"
        mock_ent2.label_ = "ORG"
        mock_ent2.start_char = 10
        mock_ent2.end_char = 17
        mock_ent2.sent = doc.sents[0]
        
        doc.ents = [mock_ent1, mock_ent2]
        return doc

# Mock spacy.load before any imports happen
def mock_spacy_load(model_name):
    """Mock function for spacy.load that returns a Language mock."""
    return MockSpacyLanguage()

# Apply the patch
spacy_patch = patch('spacy.load', side_effect=mock_spacy_load)
spacy_patch.start()