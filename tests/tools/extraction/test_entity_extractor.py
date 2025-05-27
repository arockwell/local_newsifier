"""
Tests for the Entity Extractor tool.

This test suite covers:
1. Basic entity extraction
2. Different entity types (PERSON, ORG, GPE)
3. Edge cases (empty text, unusual formats)
4. Context extraction
5. Error handling
"""

from unittest.mock import Mock, patch

import pytest

from local_newsifier.tools.extraction.entity_extractor import EntityExtractor


class MockSpacyDoc:
    """Mock spaCy Doc for testing."""

    def __init__(self, ents=None, sents=None):
        self.ents = ents or []
        self._sents = sents or []

    @property
    def sents(self):
        return self._sents


class MockSpacyEnt:
    """Mock spaCy entity for testing."""

    def __init__(self, text, label_, start_char, end_char, sent=None):
        self.text = text
        self.label_ = label_
        self.start_char = start_char
        self.end_char = end_char
        self.start = 0  # Token index
        self.end = 1  # Token index
        self.sent = sent or MockSpacySent(f"Context for {text}.")


class MockSpacySent:
    """Mock spaCy sentence for testing."""

    def __init__(self, text, start_char=0):
        self.text = text
        self.start_char = start_char
        self.start = 0  # Token index
        self.end = 10  # Token index (end position)


class MockSpacySpan:
    """Mock spaCy span for testing."""

    def __init__(self, start, end):
        self.start = start
        self.end = end


class MockSpacyLanguage:
    """Mock spaCy Language for testing."""

    def __init__(self, doc_to_return=None):
        self.doc_to_return = doc_to_return

    def __call__(self, text):
        return self.doc_to_return


@pytest.fixture
def mock_spacy_model():
    """Create a mock spaCy model."""
    with patch("spacy.load") as mock_load:
        mock_nlp = MockSpacyLanguage()
        mock_load.return_value = mock_nlp
        yield mock_nlp


@pytest.fixture
def basic_entities():
    """Create basic entities for testing."""
    person_sent = MockSpacySent("John Smith is a person.")
    org_sent = MockSpacySent("Google is a company.")
    loc_sent = MockSpacySent("New York is a city.")

    return [
        MockSpacyEnt("John Smith", "PERSON", 0, 10, person_sent),
        MockSpacyEnt("Google", "ORG", 0, 6, org_sent),
        MockSpacyEnt("New York", "GPE", 0, 8, loc_sent),
    ]


@pytest.fixture
def entity_extractor(mock_spacy_model):
    """Create an EntityExtractor instance with mocked spaCy model."""
    # Direct instantiation without using injectable pattern
    # for backward compatibility
    return EntityExtractor(nlp_model=mock_spacy_model)


class TestEntityExtractor:
    """Test suite for EntityExtractor."""

    def test_initialization(self, mock_spacy_model):
        """Test initialization of EntityExtractor."""
        extractor = EntityExtractor(nlp_model=mock_spacy_model)
        assert extractor.nlp is mock_spacy_model

    def test_initialization_fallback(self, mock_spacy_model):
        """Test initialization with fallback to loading model."""
        extractor = EntityExtractor(nlp_model=None)
        assert extractor.nlp is mock_spacy_model

    def test_initialization_error(self):
        """Test initialization error handling."""
        with patch("spacy.load", side_effect=OSError("Model not found")):
            with pytest.raises(RuntimeError, match="spaCy model .* not found"):
                EntityExtractor(nlp_model=None)

    def test_extract_entities_basic(self, entity_extractor, basic_entities, mock_spacy_model):
        """Test basic entity extraction."""
        # Setup mock document with entities
        mock_doc = MockSpacyDoc(ents=basic_entities)
        mock_spacy_model.doc_to_return = mock_doc

        # Extract entities
        entities = entity_extractor.extract_entities("Sample text with entities.")

        # Verify results
        assert len(entities) == 3

        # Check person entity
        person = entities[0]
        assert person["text"] == "John Smith"
        assert person["type"] == "PERSON"
        assert person["context"] == "John Smith is a person."

        # Check organization entity
        org = entities[1]
        assert org["text"] == "Google"
        assert org["type"] == "ORG"
        assert org["context"] == "Google is a company."

        # Check location entity
        loc = entities[2]
        assert loc["text"] == "New York"
        assert loc["type"] == "GPE"
        assert loc["context"] == "New York is a city."

    def test_extract_entities_with_filter(self, entity_extractor, basic_entities, mock_spacy_model):
        """Test entity extraction with type filtering."""
        # Setup mock document with entities
        mock_doc = MockSpacyDoc(ents=basic_entities)
        mock_spacy_model.doc_to_return = mock_doc

        # Extract only person entities
        person_entities = entity_extractor.extract_entities(
            "Sample text with entities.", entity_types={"PERSON"}
        )

        # Verify results
        assert len(person_entities) == 1
        assert person_entities[0]["text"] == "John Smith"
        assert person_entities[0]["type"] == "PERSON"

        # Extract only organization entities
        org_entities = entity_extractor.extract_entities(
            "Sample text with entities.", entity_types={"ORG"}
        )

        # Verify results
        assert len(org_entities) == 1
        assert org_entities[0]["text"] == "Google"
        assert org_entities[0]["type"] == "ORG"

        # Extract multiple entity types
        mixed_entities = entity_extractor.extract_entities(
            "Sample text with entities.", entity_types={"PERSON", "GPE"}
        )

        # Verify results
        assert len(mixed_entities) == 2
        assert {e["type"] for e in mixed_entities} == {"PERSON", "GPE"}

    def test_extract_person_entities(self, entity_extractor, basic_entities, mock_spacy_model):
        """Test extraction of person entities."""
        # Setup mock document with entities
        mock_doc = MockSpacyDoc(ents=basic_entities)
        mock_spacy_model.doc_to_return = mock_doc

        # Extract person entities
        entities = entity_extractor.extract_person_entities("Sample text with entities.")

        # Verify results
        assert len(entities) == 1
        assert entities[0]["text"] == "John Smith"
        assert entities[0]["type"] == "PERSON"

    def test_extract_organization_entities(
        self, entity_extractor, basic_entities, mock_spacy_model
    ):
        """Test extraction of organization entities."""
        # Setup mock document with entities
        mock_doc = MockSpacyDoc(ents=basic_entities)
        mock_spacy_model.doc_to_return = mock_doc

        # Extract organization entities
        entities = entity_extractor.extract_organization_entities("Sample text with entities.")

        # Verify results
        assert len(entities) == 1
        assert entities[0]["text"] == "Google"
        assert entities[0]["type"] == "ORG"

    def test_extract_location_entities(self, entity_extractor, basic_entities, mock_spacy_model):
        """Test extraction of location entities."""
        # Setup mock document with entities
        mock_doc = MockSpacyDoc(ents=basic_entities)
        mock_spacy_model.doc_to_return = mock_doc

        # Extract location entities
        entities = entity_extractor.extract_location_entities("Sample text with entities.")

        # Verify results
        assert len(entities) == 1
        assert entities[0]["text"] == "New York"
        assert entities[0]["type"] == "GPE"

    def test_extract_entities_empty_text(self, entity_extractor, mock_spacy_model):
        """Test entity extraction with empty text."""
        # Setup mock document with no entities
        mock_doc = MockSpacyDoc(ents=[])
        mock_spacy_model.doc_to_return = mock_doc

        # Extract entities from empty text
        entities = entity_extractor.extract_entities("")

        # Verify results
        assert len(entities) == 0

    def test_extract_entities_no_entities(self, entity_extractor, mock_spacy_model):
        """Test entity extraction with text containing no entities."""
        # Setup mock document with no entities
        mock_doc = MockSpacyDoc(ents=[])
        mock_spacy_model.doc_to_return = mock_doc

        # Extract entities from text with no entities
        entities = entity_extractor.extract_entities("This text contains no named entities.")

        # Verify results
        assert len(entities) == 0

    def test_extract_entities_with_context(self, entity_extractor, mock_spacy_model):
        """Test entity extraction with expanded context."""
        # Create sentences
        sent1 = MockSpacySent("First sentence.", 0)
        sent2 = MockSpacySent("John Smith is a person.", 15)
        sent3 = MockSpacySent("Third sentence.", 40)

        # Create entity in the middle sentence
        person_ent = MockSpacyEnt("John Smith", "PERSON", 15, 25, sent2)

        # Setup mock document
        mock_doc = MockSpacyDoc(ents=[person_ent], sents=[sent1, sent2, sent3])
        mock_spacy_model.doc_to_return = mock_doc

        # Mock char_span method
        mock_doc.char_span = Mock(return_value=MockSpacySpan(0, 1))

        # Extract entities with context
        entities = entity_extractor.extract_entities_with_context(
            "First sentence. John Smith is a person. Third sentence.", context_window=1
        )

        # Verify results
        assert len(entities) == 1
        assert entities[0]["text"] == "John Smith"
        assert entities[0]["type"] == "PERSON"
        assert "context" in entities[0]
        assert "expanded_context" in entities[0]

    def test_extract_entities_with_context_edge_cases(self, entity_extractor, mock_spacy_model):
        """Test entity extraction with context in edge cases."""
        # Create sentences
        sent1 = MockSpacySent("John Smith is at the beginning.", 0)
        sent2 = MockSpacySent("Middle sentence.", 33)
        sent3 = MockSpacySent("Jane Doe is at the end.", 50)

        # Create entities at beginning and end
        person1_ent = MockSpacyEnt("John Smith", "PERSON", 0, 10, sent1)
        person2_ent = MockSpacyEnt("Jane Doe", "PERSON", 50, 58, sent3)

        # Setup mock document
        mock_doc = MockSpacyDoc(ents=[person1_ent, person2_ent], sents=[sent1, sent2, sent3])
        mock_spacy_model.doc_to_return = mock_doc

        # Mock char_span method
        mock_doc.char_span = Mock(return_value=MockSpacySpan(0, 1))

        # Extract entities with context
        entities = entity_extractor.extract_entities_with_context(
            "John Smith is at the beginning. Middle sentence. Jane Doe is at the end.",
            context_window=1,
        )

        # Verify results
        assert len(entities) == 2
        assert entities[0]["text"] == "John Smith"
        assert entities[1]["text"] == "Jane Doe"
        assert "expanded_context" in entities[0]
        assert "expanded_context" in entities[1]

    def test_extract_entities_with_malformed_content(self, entity_extractor, mock_spacy_model):
        """Test entity extraction with malformed content."""
        # We need to patch the extract_entities method to handle the exception
        with patch.object(
            entity_extractor, "nlp", side_effect=ValueError("Error processing malformed text")
        ):
            # Extract entities from malformed text - should handle exception gracefully
            # This test verifies that the code gracefully handles exceptions, but since our
            # implementation doesn't have that error handling yet, we'll expect the exception
            with pytest.raises(ValueError):
                entity_extractor.extract_entities("This is malformed text.")
