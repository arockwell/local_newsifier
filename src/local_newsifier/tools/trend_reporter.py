"""Tool for generating reports and visualizations of news trends."""

import json
import os
import logging
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union, Any, TYPE_CHECKING

from local_newsifier.models.trend import TimeFrame, TrendAnalysis, TrendType

if TYPE_CHECKING:
    from local_newsifier.tools.file_writer import FileWriterTool

logger = logging.getLogger(__name__)


class ReportFormat(str, Enum):
    """Report output formats."""

    JSON = "json"
    MARKDOWN = "markdown"
    TEXT = "text"


class TrendReporter:
    """Tool for creating reports of detected trends."""

    def __init__(self, output_dir: str = "output"):
        """
        Initialize the trend reporter.

        Args:
            output_dir: Directory for report output
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        # FileWriterTool will be injected in the injectable pattern
        self.file_writer = None

    def generate_trend_summary(
        self, trends: List[TrendAnalysis], format: ReportFormat = ReportFormat.TEXT
    ) -> str:
        """
        Generate a summary of detected trends.

        Args:
            trends: List of trend analysis objects
            format: Output format

        Returns:
            Formatted summary text
        """
        if not trends:
            return "No significant trends detected in the analyzed time period."

        if format == ReportFormat.JSON:
            return self._generate_json_summary(trends)
        elif format == ReportFormat.MARKDOWN:
            return self._generate_markdown_summary(trends)
        else:  # TEXT
            return self._generate_text_summary(trends)

    def _generate_text_summary(self, trends: List[TrendAnalysis]) -> str:
        """Generate text format summary."""
        summary = f"LOCAL NEWS TRENDS REPORT - {datetime.now().strftime('%Y-%m-%d')}\n\n"
        summary += f"Found {len(trends)} significant trends in local news coverage.\n\n"

        for i, trend in enumerate(trends, 1):
            summary += f"{i}. {trend.name} (Confidence: {trend.confidence_score:.2f})\n"
            summary += f"   Type: {trend.trend_type.replace('_', ' ').title()}\n"
            summary += f"   {trend.description}\n"
            
            if trend.entities and len(trend.entities) > 1:
                summary += "   Related entities:\n"
                for entity in trend.entities[1:4]:  # Show up to 3 related entities
                    summary += f"   - {entity.text} ({entity.entity_type})\n"
            
            if trend.evidence:
                summary += "   Supporting evidence:\n"
                for ev in trend.evidence[:3]:  # Show up to 3 evidence items
                    date_str = ev.published_at.strftime("%Y-%m-%d")
                    summary += f"   - [{date_str}] {ev.article_title or 'Untitled article'}\n"
            
            summary += "\n"

        return summary

    def _generate_markdown_summary(self, trends: List[TrendAnalysis]) -> str:
        """Generate markdown format summary."""
        summary = f"# Local News Trends Report - {datetime.now().strftime('%Y-%m-%d')}\n\n"
        summary += f"Found **{len(trends)}** significant trends in local news coverage.\n\n"

        for trend in trends:
            summary += f"## {trend.name}\n\n"
            summary += f"**Type:** {trend.trend_type.replace('_', ' ').title()}  \n"
            summary += f"**Confidence:** {trend.confidence_score:.2f}  \n"
            summary += f"**Description:** {trend.description}  \n\n"
            
            if trend.tags:
                tags = " ".join([f"#{tag}" for tag in trend.tags])
                summary += f"**Tags:** {tags}  \n\n"
            
            if trend.entities and len(trend.entities) > 1:
                summary += "### Related entities\n\n"
                for entity in trend.entities[1:]:
                    summary += f"- **{entity.text}** ({entity.entity_type}) - Relevance: {entity.relevance_score:.2f}\n"
                summary += "\n"
            
            if trend.evidence:
                summary += "### Supporting evidence\n\n"
                for ev in trend.evidence:
                    date_str = ev.published_at.strftime("%Y-%m-%d")
                    title = ev.article_title or "Untitled article"
                    summary += f"- [{title}]({ev.article_url}) - {date_str}\n"
                summary += "\n"
                
            # Add frequency data if available
            if trend.frequency_data:
                summary += "### Frequency over time\n\n"
                summary += "| Date | Mentions |\n"
                summary += "|------|----------|\n"
                for date, count in sorted(trend.frequency_data.items()):
                    summary += f"| {date} | {count} |\n"
                summary += "\n"
            
            summary += "---\n\n"

        summary += f"*Report generated at {datetime.now().isoformat()}*"
        return summary

    def _generate_json_summary(self, trends: List[TrendAnalysis]) -> str:
        """Generate JSON format summary."""
        trend_data = []
        
        for trend in trends:
            # Convert the trend to a dict
            trend_dict = {
                "id": str(trend.trend_id),
                "name": trend.name,
                "type": trend.trend_type,
                "description": trend.description,
                "confidence": trend.confidence_score,
                "status": trend.status,
                "start_date": trend.start_date.isoformat(),
                "statistical_significance": trend.statistical_significance,
                "tags": trend.tags,
                "entities": [
                    {
                        "text": entity.text,
                        "type": entity.entity_type,
                        "frequency": entity.frequency,
                        "relevance": entity.relevance_score,
                    }
                    for entity in trend.entities
                ],
                "evidence": [
                    {
                        "url": ev.article_url,
                        "title": ev.article_title,
                        "date": ev.published_at.isoformat(),
                        "text": ev.evidence_text,
                    }
                    for ev in trend.evidence
                ],
                "frequency_data": trend.frequency_data,
            }
            
            trend_data.append(trend_dict)
            
        return json.dumps(
            {
                "report_date": datetime.now().isoformat(),
                "trend_count": len(trends),
                "trends": trend_data,
            },
            indent=2,
        )

    def save_report(
        self,
        trends: List[TrendAnalysis],
        filename: Optional[str] = None,
        format: ReportFormat = ReportFormat.TEXT,
    ) -> str:
        """
        Generate and save a report to file.

        Args:
            trends: List of trend analysis objects
            filename: Output filename (defaults to "trend_report_{date}.{ext}")
            format: Output format

        Returns:
            Path to the saved report file
        """
        # Generate report content
        content = self.generate_trend_summary(trends, format)

        # Determine file extension
        ext = format.value

        # Create filename if not provided
        if not filename:
            date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"trend_report_{date_str}.{ext}"

        # Ensure it has the right extension
        if not filename.endswith(f".{ext}"):
            filename = f"{filename}.{ext}"

        # Full path
        filepath = os.path.join(self.output_dir, filename)

        # Use file_writer if available, otherwise write directly
        if self.file_writer:
            import logging
            logging.debug(f"Using file_writer to write report to {filepath}")
            return self.file_writer.write_file(filepath, content)
        else:
            # Save file directly
            with open(filepath, "w") as f:
                f.write(content)

            return filepath


# Apply the injectable decorator conditionally at the end of the file
# This ensures it's only applied in non-test environments
try:
    # Only apply in non-test environments
    if not os.environ.get('PYTEST_CURRENT_TEST'):
        from fastapi_injectable import injectable
        TrendReporter = injectable(use_cache=False)(TrendReporter)
except (ImportError, Exception) as e:
    logger.debug(f"Skipping injectable decorator application for TrendReporter: {e}")
    pass