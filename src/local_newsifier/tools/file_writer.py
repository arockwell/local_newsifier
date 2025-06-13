"""Helper for writing analysis results to disk."""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

from fastapi_injectable import injectable

from local_newsifier.models.state import AnalysisStatus, NewsAnalysisState
from local_newsifier.utils.dates import get_utc_now, to_iso_string
from local_newsifier.utils.url import extract_source_from_url


@injectable(use_cache=False)
class FileWriterTool:
    """Tool for saving analysis results to files with atomic writes."""

    def __init__(self, output_dir: str = "output"):
        """
        Initialize the file writer.

        Args:
            output_dir: Directory to save results in
        """
        self.output_dir = Path(output_dir)
        self._ensure_output_dir()

    def _ensure_output_dir(self) -> None:
        """Ensure the output directory exists."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _generate_filename(self, state: NewsAnalysisState) -> str:
        """
        Generate a filename for the results.

        Args:
            state: Current pipeline state

        Returns:
            Filename string
        """
        # Extract domain from URL
        domain = extract_source_from_url(state.target_url).replace("www.", "")

        # Create timestamp
        timestamp = get_utc_now().strftime("%Y%m%d_%H%M%S")

        return f"{domain}_{timestamp}_{state.run_id}.json"

    def _prepare_output(self, state: NewsAnalysisState) -> Dict[str, Any]:
        """
        Prepare the output dictionary.

        Args:
            state: Current pipeline state

        Returns:
            Dictionary to save
        """
        return {
            "run_id": str(state.run_id),
            "url": state.target_url,
            "scraping": {
                "timestamp": to_iso_string(state.scraped_at),
                "success": state.status
                in [AnalysisStatus.SCRAPE_SUCCEEDED, AnalysisStatus.COMPLETED_SUCCESS],
                "text_length": len(state.scraped_text) if state.scraped_text else 0,
            },
            "analysis": {
                "timestamp": to_iso_string(state.analyzed_at),
                "success": state.status
                in [
                    AnalysisStatus.ANALYSIS_SUCCEEDED,
                    AnalysisStatus.COMPLETED_SUCCESS,
                ],
                "config": state.analysis_config,
                "results": state.analysis_results,
            },
            "metadata": {
                "created_at": to_iso_string(state.created_at),
                "completed_at": to_iso_string(state.last_updated),
                "status": state.status,
                "error": (
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

    def save(self, state: NewsAnalysisState) -> NewsAnalysisState:
        """
        Save analysis results to file.

        Args:
            state: Current pipeline state

        Returns:
            Updated state
        """
        try:
            state.status = AnalysisStatus.SAVING
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

            state.save_path = str(filepath)
            state.saved_at = get_utc_now()
            state.status = AnalysisStatus.SAVE_SUCCEEDED
            state.add_log(f"Successfully saved results to {filepath}")

            # If everything succeeded, mark as complete
            if state.status == AnalysisStatus.SAVE_SUCCEEDED and not state.error_details:
                state.status = AnalysisStatus.COMPLETED_SUCCESS
            else:
                state.status = AnalysisStatus.COMPLETED_WITH_ERRORS

        except Exception as e:
            state.status = AnalysisStatus.SAVE_FAILED
            state.set_error("saving", e)
            state.add_log(f"Error saving results: {str(e)}")
            raise

        return state
