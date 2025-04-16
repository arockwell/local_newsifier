"""Script to test headline trend analysis and generate reports."""

import logging
import os
from datetime import datetime, timedelta, UTC

from local_newsifier.database.engine import get_session
from local_newsifier.tools.analysis.headline_analyzer import HeadlineTrendAnalyzer

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Ensure output directory exists
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def format_report(trends: dict, format_type: str) -> str:
    """Format trend analysis results into a report."""
    if format_type == "text":
        return _format_text_report(trends)
    elif format_type == "markdown":
        return _format_markdown_report(trends)
    elif format_type == "html":
        return _format_html_report(trends)
    else:
        raise ValueError(f"Unsupported format type: {format_type}")

def _format_text_report(trends: dict) -> str:
    """Format trend analysis results as plain text."""
    lines = ["HEADLINE TREND ANALYSIS REPORT", "=" * 30, ""]
    
    if "error" in trends:
        lines.extend(["Error:", trends["error"], ""])
        return "\n".join(lines)
    
    # Trending terms
    lines.extend(["TOP TRENDING TERMS", "-" * 20])
    for term in trends.get("trending_terms", []):
        lines.append(
            f"{term['term']}: {term['growth_rate']:.1f}x growth "
            f"({term['first_count']} → {term['last_count']} mentions)"
        )
    lines.append("")
    
    # Overall top terms
    lines.extend(["OVERALL TOP TERMS", "-" * 20])
    for term, count in trends.get("overall_top_terms", []):
        lines.append(f"{term}: {count} mentions")
    lines.append("")
    
    # Article counts
    lines.extend(["ARTICLE COUNTS BY PERIOD", "-" * 20])
    for period, count in trends.get("period_counts", {}).items():
        lines.append(f"{period}: {count} articles")
    
    return "\n".join(lines)

def _format_markdown_report(trends: dict) -> str:
    """Format trend analysis results as markdown."""
    lines = ["# Headline Trend Analysis Report", ""]
    
    if "error" in trends:
        lines.extend([f"**Error:** {trends['error']}", ""])
        return "\n".join(lines)
    
    # Trending terms
    lines.extend(["## Top Trending Terms", ""])
    for term in trends.get("trending_terms", []):
        lines.append(
            f"- **{term['term']}**: {term['growth_rate']:.1f}x growth "
            f"({term['first_count']} → {term['last_count']} mentions)"
        )
    lines.append("")
    
    # Overall top terms
    lines.extend(["## Overall Top Terms", ""])
    for term, count in trends.get("overall_top_terms", []):
        lines.append(f"- **{term}**: {count} mentions")
    lines.append("")
    
    # Article counts
    lines.extend([
        "## Article Counts by Period", "",
        "| Period | Article Count |",
        "|--------|---------------|"
    ])
    for period, count in trends.get("period_counts", {}).items():
        lines.append(f"| {period} | {count} |")
    
    return "\n".join(lines)

def _format_html_report(trends: dict) -> str:
    """Format trend analysis results as HTML."""
    lines = [
        "<html>",
        "<head>",
        "<style>",
        "body { font-family: Arial, sans-serif; margin: 2em; }",
        "h1, h2 { color: #333; }",
        "table { border-collapse: collapse; margin: 1em 0; }",
        "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
        "th { background-color: #f5f5f5; }",
        "</style>",
        "</head>",
        "<body>",
        "<h1>Headline Trend Analysis Report</h1>"
    ]
    
    if "error" in trends:
        lines.extend([
            f"<p><strong>Error:</strong> {trends['error']}</p>",
            "</body>",
            "</html>"
        ])
        return "\n".join(lines)
    
    # Trending terms
    lines.extend([
        "<h2>Top Trending Terms</h2>",
        "<ul>"
    ])
    for term in trends.get("trending_terms", []):
        lines.append(
            f"<li><strong>{term['term']}</strong>: {term['growth_rate']:.1f}x growth "
            f"({term['first_count']} → {term['last_count']} mentions)</li>"
        )
    lines.append("</ul>")
    
    # Overall top terms
    lines.extend([
        "<h2>Overall Top Terms</h2>",
        "<ul>"
    ])
    for term, count in trends.get("overall_top_terms", []):
        lines.append(f"<li><strong>{term}</strong>: {count} mentions</li>")
    lines.append("</ul>")
    
    # Article counts
    lines.extend([
        "<h2>Article Counts by Period</h2>",
        "<table>",
        "<tr><th>Period</th><th>Article Count</th></tr>"
    ])
    for period, count in trends.get("period_counts", {}).items():
        lines.append(f"<tr><td>{period}</td><td>{count}</td></tr>")
    lines.extend([
        "</table>",
        "</body>",
        "</html>"
    ])
    
    return "\n".join(lines)

def generate_reports(analyzer: HeadlineTrendAnalyzer, start_date: datetime, end_date: datetime):
    """Generate trend reports in different formats."""
    # Generate daily trends report
    daily_trends = analyzer.analyze_trends(
        start_date=start_date,
        end_date=end_date,
        time_interval="day",
        top_n=20
    )
    
    # Generate weekly trends report
    weekly_trends = analyzer.analyze_trends(
        start_date=start_date,
        end_date=end_date,
        time_interval="week",
        top_n=20
    )
    
    # Save reports in different formats
    formats = ["text", "markdown", "html"]
    for fmt in formats:
        # Daily trends
        daily_filename = os.path.join(OUTPUT_DIR, f"daily_trends.{fmt}")
        with open(daily_filename, "w") as f:
            f.write(format_report(daily_trends, format_type=fmt))
        logger.info(f"Generated daily trends report: {daily_filename}")
        
        # Weekly trends
        weekly_filename = os.path.join(OUTPUT_DIR, f"weekly_trends.{fmt}")
        with open(weekly_filename, "w") as f:
            f.write(format_report(weekly_trends, format_type=fmt))
        logger.info(f"Generated weekly trends report: {weekly_filename}")

def main():
    """Run headline trend analysis and generate reports."""
    with get_session() as session:
        try:
            # Create analyzer
            analyzer = HeadlineTrendAnalyzer(session=session)
            
            # Set date range for analysis (last 30 days)
            end_date = datetime.now(UTC)
            start_date = end_date - timedelta(days=30)
            
            # Generate reports
            generate_reports(analyzer, start_date, end_date)
            logger.info("Successfully generated all trend reports")
            
        except Exception as e:
            logger.error(f"Error generating trend reports: {e}")

if __name__ == "__main__":
    main() 