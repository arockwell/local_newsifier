from datetime import datetime, timezone
from typing import Dict, List, Set

import spacy
from spacy.language import Language

from local_newsifier.models.state import AnalysisStatus, NewsAnalysisState


class NERAnalyzerTool:
    """Tool for performing Named Entity Recognition using spaCy."""

    def __init__(self, model_name: str = "en_core_web_lg"):
        """
        Initialize the NER analyzer.

        Args:
            model_name: Name of the spaCy model to use
        """
        try:
            self.nlp: Language = spacy.load(model_name)
        except OSError:
            raise RuntimeError(
                f"spaCy model '{model_name}' not found. "
                f"Please install it using: python -m spacy download {model_name}"
            )

    def _extract_entities(
        self, text: str, entity_types: List[str]
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Extract named entities from text.

        Args:
            text: Text to analyze
            entity_types: List of entity types to extract (e.g., ["PERSON", "ORG"])

        Returns:
            Dictionary mapping entity types to lists of found entities
        """
        doc = self.nlp(text)

        # Initialize results dictionary
        results: Dict[str, List[Dict[str, str]]] = {
            entity_type: [] for entity_type in entity_types
        }

        # Track seen entities to avoid duplicates
        seen_entities: Dict[str, Set[str]] = {
            entity_type: set() for entity_type in entity_types
        }

        for ent in doc.ents:
            if ent.label_ in entity_types:
                # Skip if we've seen this exact entity text for this type
                if ent.text in seen_entities[ent.label_]:
                    continue

                seen_entities[ent.label_].add(ent.text)

                # Add entity with context
                sent = ent.sent.text
                start_char = ent.start_char - ent.sent.start_char
                end_char = ent.end_char - ent.sent.start_char

                entity_info = {
                    "text": ent.text,
                    "sentence": sent,
                    "start": start_char,
                    "end": end_char,
                }

                results[ent.label_].append(entity_info)

        return results

    def analyze(self, state: NewsAnalysisState) -> NewsAnalysisState:
        """
        Analyze article content for named entities.

        Args:
            state: Current pipeline state

        Returns:
            Updated state
        """
        try:
            state.status = AnalysisStatus.ANALYZING
            state.add_log("Starting NER analysis")

            if not state.scraped_text:
                raise ValueError("No text content available for analysis")

            entity_types = state.analysis_config.get(
                "entity_types", ["PERSON", "ORG", "GPE"]
            )

            results = self._extract_entities(
                text=state.scraped_text, entity_types=entity_types
            )

            # Add summary statistics
            entity_counts = {
                entity_type: len(entities) for entity_type, entities in results.items()
            }

            state.analysis_results = {
                "entities": results,
                "statistics": {
                    "entity_counts": entity_counts,
                    "total_entities": sum(entity_counts.values()),
                },
            }

            state.analyzed_at = datetime.now(timezone.utc)
            state.status = AnalysisStatus.ANALYSIS_SUCCEEDED
            state.add_log(
                f"Successfully completed NER analysis. "
                f"Found {state.analysis_results['statistics']['total_entities']} entities."
            )

        except Exception as e:
            state.status = AnalysisStatus.ANALYSIS_FAILED
            state.set_error("analysis", e)
            state.add_log(f"Error during NER analysis: {str(e)}")
            raise

        return state
