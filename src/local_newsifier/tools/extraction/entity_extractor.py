"""Entity extraction tool for extracting entities from text content."""

from typing import Any, Dict, List, Optional, Set

import spacy
from fastapi import Depends
from fastapi_injectable import injectable
from spacy.language import Language
from spacy.tokens import Doc, Span


@injectable(use_cache=False)
class EntityExtractor:
    """Tool for extracting entities from text content."""

    def __init__(self, nlp_model: Optional[Any] = None, model_name: str = "en_core_web_lg"):
        """Initialize with spaCy model.

        Args:
            nlp_model: Pre-loaded spaCy NLP model (injected)
            model_name: Name of the spaCy model to use as fallback
        """
        self.nlp = nlp_model

        # Fallback to loading model if not injected (for backward compatibility)
        if self.nlp is None:
            try:
                self.nlp: Language = spacy.load(model_name)
            except OSError:
                raise RuntimeError(
                    f"spaCy model '{model_name}' not found. "
                    f"Please install it using: python -m spacy download {model_name}"
                )

    def extract_entities(self, content: str, entity_types: Optional[Set[str]] = None) -> List[Dict]:
        """
        Extract entities from text content.

        Args:
            content: Text content to analyze
            entity_types: Optional set of entity types to include (e.g., {"PERSON", "ORG"})
                          If None, all entity types are included

        Returns:
            List of extracted entities with metadata
        """
        doc = self.nlp(content)
        entities = []

        for ent in doc.ents:
            # Filter by entity type if specified
            if entity_types and ent.label_ not in entity_types:
                continue

            # Extract entity data
            entity_data = {
                "text": ent.text,
                "type": ent.label_,
                "start_char": ent.start_char,
                "end_char": ent.end_char,
                "context": ent.sent.text,
                "confidence": 1.0,  # Default confidence, could be refined
            }

            entities.append(entity_data)

        return entities

    def extract_person_entities(self, content: str) -> List[Dict]:
        """Extract only person entities from text content.

        Args:
            content: Text content to analyze

        Returns:
            List of extracted person entities with metadata
        """
        return self.extract_entities(content, entity_types={"PERSON"})

    def extract_organization_entities(self, content: str) -> List[Dict]:
        """Extract only organization entities from text content.

        Args:
            content: Text content to analyze

        Returns:
            List of extracted organization entities with metadata
        """
        return self.extract_entities(content, entity_types={"ORG"})

    def extract_location_entities(self, content: str) -> List[Dict]:
        """Extract only location entities from text content.

        Args:
            content: Text content to analyze

        Returns:
            List of extracted location entities with metadata
        """
        return self.extract_entities(content, entity_types={"GPE", "LOC"})

    def extract_entities_with_context(
        self, content: str, entity_types: Optional[Set[str]] = None, context_window: int = 1
    ) -> List[Dict]:
        """
        Extract entities with expanded context.

        Args:
            content: Text content to analyze
            entity_types: Optional set of entity types to include
            context_window: Number of sentences before and after to include in context

        Returns:
            List of extracted entities with expanded context
        """
        # First extract basic entities
        entities = self.extract_entities(content, entity_types)

        # Process document once
        doc = self.nlp(content)

        # Convert sentences to list for indexing
        sentences = list(doc.sents)

        # Map start character positions to sentence indices
        sent_indices = {}
        for i, sent in enumerate(sentences):
            sent_indices[sent.start_char] = i

        # Expand context for each entity
        for entity in entities:
            # Find the entity in the document
            entity_span = doc.char_span(
                entity["start_char"], entity["end_char"], alignment_mode="expand"
            )

            if entity_span:
                # Find the sentence containing this entity
                for sent in doc.sents:
                    if entity_span.start >= sent.start and entity_span.end <= sent.end:
                        sent_idx = sent_indices[sent.start_char]

                        # Collect context sentences
                        context_sents = []
                        start_idx = max(0, sent_idx - context_window)
                        end_idx = min(len(sentences), sent_idx + context_window + 1)

                        for i in range(start_idx, end_idx):
                            context_sents.append(sentences[i].text)

                        # Update context with expanded window
                        entity["expanded_context"] = " ".join(context_sents)
                        break

        return entities
