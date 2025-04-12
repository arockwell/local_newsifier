#!/usr/bin/env python3
"""Script for running the news analysis pipeline."""

import argparse
import logging
import sys
from pathlib import Path

# Add src directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from local_newsifier.flows.news_pipeline import NewsPipelineFlow
from local_newsifier.models.state import AnalysisStatus


def setup_logging(level: int = logging.INFO) -> None:
    """Set up logging configuration."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('pipeline.log')
        ]
    )


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run news analysis pipeline")
    parser.add_argument("--url", required=True, help="URL of the article to analyze")
    parser.add_argument("--output-dir", default="output", help="Directory to save results")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    # Set up logging
    setup_logging(level=logging.DEBUG if args.debug else logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        # Initialize and run pipeline
        flow = NewsPipelineFlow(output_dir=args.output_dir)
        state = flow.start_pipeline(url=args.url)

        # Log results
        if state.status == AnalysisStatus.COMPLETED_SUCCESS:
            logger.info(
                "Pipeline completed successfully. "
                f"Results saved to: {state.save_path}"
            )
            sys.exit(0)
        else:
            logger.error(
                f"Pipeline completed with errors. Final status: {state.status}"
            )
            if state.error_details:
                logger.error(
                    f"Error in {state.error_details.task}: "
                    f"{state.error_details.message}"
                )
            sys.exit(1)

    except Exception as e:
        logger.exception("Unhandled error in pipeline")
        sys.exit(1)


if __name__ == "__main__":
    main() 