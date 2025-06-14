"""File writer tool using the new ProcessingState model.

This is an example of how to migrate from NewsAnalysisState to ProcessingState.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

from fastapi_injectable import injectable

from local_newsifier.models.processing_state import ProcessingState, ProcessingStatus
from local_newsifier.utils.dates import get_utc_now, to_iso_string
from local_newsifier.utils.url import extract_source_from_url


@injectable(use_cache=False)
class FileWriterToolV2:
    """Tool for saving analysis results to files using ProcessingState."""

    def __init__(self, output_dir: str = "output"):
        """Initialize the file writer."""
        self.output_dir = Path(output_dir)
        self._ensure_output_dir()

    def _ensure_output_dir(self) -> None:
        """Ensure the output directory exists."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _generate_filename(self, state: ProcessingState) -> str:
        """Generate a filename for the results."""
        # Extract domain from URL
        domain = extract_source_from_url(state.target_url).replace("www.", "")

        # Create timestamp
        timestamp = get_utc_now().strftime("%Y%m%d_%H%M%S")

        return f"{domain}_{timestamp}_{state.run_id}.json"

    def _prepare_output(self, state: ProcessingState) -> Dict[str, Any]:
        """Prepare the output dictionary."""
        # Get data from the generic state
        scraped_at = state.get_data("scraped_at")
        scraped_text = state.get_data("scraped_text", "")
        analyzed_at = state.get_data("analyzed_at")
        analysis_config = state.get_data("analysis_config", {})
        analysis_results = state.get_data("analysis_results", {})

        return {
            "run_id": str(state.run_id),
            "url": state.target_url,
            "processing_type": state.processing_type,
            "scraping": {
                "timestamp": to_iso_string(scraped_at),
                "success": state.status
                in [ProcessingStatus.SCRAPE_SUCCEEDED, ProcessingStatus.COMPLETED_SUCCESS],
                "text_length": len(scraped_text),
            },
            "analysis": {
                "timestamp": to_iso_string(analyzed_at),
                "success": state.status
                in [ProcessingStatus.ANALYSIS_SUCCEEDED, ProcessingStatus.COMPLETED_SUCCESS],
                "config": analysis_config,
                "results": analysis_results,
            },
            "metadata": {
                "created_at": to_iso_string(state.created_at),
                "completed_at": to_iso_string(state.completed_at),
                "status": state.status.value,
                "errors": state.errors,
                "error_details": (
                    {
                        "task": state.error_details.task,
                        "type": state.error_details.type,
                        "message": state.error_details.message,
                    }
                    if state.error_details
                    else None
                ),
            },
        }

    def save(self, state: ProcessingState) -> ProcessingState:
        """Save analysis results to file."""
        try:
            state.status = ProcessingStatus.SAVING
            state.add_log("Starting to save results")

            filename = self._generate_filename(state)
            filepath = self.output_dir / filename

            # Prepare output data
            output_data = self._prepare_output(state)

            # Create temporary file
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
                # Write to temporary file
                json.dump(output_data, temp_file, indent=2)
                temp_file.flush()
                os.fsync(temp_file.fileno())

                # Atomic rename
                os.replace(temp_file.name, filepath)

            state.set_data("save_path", str(filepath))
            state.set_data("saved_at", get_utc_now())
            state.status = ProcessingStatus.SAVE_SUCCEEDED
            state.add_log(f"Successfully saved results to {filepath}")

            # If everything succeeded, mark as complete
            if state.status == ProcessingStatus.SAVE_SUCCEEDED and not state.error_details:
                state.complete_processing(success=True)

        except Exception as e:
            state.status = ProcessingStatus.SAVE_FAILED
            state.set_error("saving", e)
            state.add_error(f"Error saving results: {str(e)}")
            raise

        return state
