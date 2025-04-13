# Local News Trends Analysis

## Overview
This PR adds new functionality for detecting and analyzing trends in local news coverage over time. It enables the system to identify emerging topics, frequency spikes, novel entities, and sustained coverage patterns in news articles, providing valuable insights into evolving local news narratives.

## Key Components

### Models
- `TrendAnalysis` - Represents a detected trend with supporting evidence
- `TopicFrequency` - Tracks frequency data for topics over time
- `TrendAnalysisConfig` - Configuration settings for trend analysis

### Tools
- `HistoricalDataAggregator` - Retrieves and organizes historical article data
- `TopicFrequencyAnalyzer` - Analyzes statistical significance of topic frequency changes
- `TrendDetector` - Applies algorithms to identify various trend types
- `TrendReporter` - Generates reports and visualizations of detected trends

### Flow
- `NewsTrendAnalysisFlow` - Orchestrates the trend analysis process

## Implementation Features
- Statistical analysis to identify significant frequency changes
- Support for different time frames (day, week, month, etc.)
- Pattern recognition for rising, falling, and consistent trends
- Related topic discovery
- Customizable trend reporting in multiple formats (markdown, JSON, text)

## Test Coverage
The implementation includes comprehensive test coverage with unit tests for all components:
- Model validation and behavior tests
- Tool functionality tests with mocked dependencies
- Flow orchestration tests

## How to Use
```python
from src.local_newsifier.flows.trend_analysis_flow import NewsTrendAnalysisFlow, ReportFormat
from src.local_newsifier.models.trend import TrendAnalysisConfig, TimeFrame

# Create configuration
config = TrendAnalysisConfig(
    time_frame=TimeFrame.WEEK,
    min_articles=3,
    entity_types=["PERSON", "ORG", "GPE"],
    significance_threshold=1.5
)

# Initialize flow
flow = NewsTrendAnalysisFlow(config=config)

# Run analysis
state = flow.run_analysis(report_format=ReportFormat.MARKDOWN)

# Access results
if state.detected_trends:
    print(f"Found {len(state.detected_trends)} trends")
    for trend in state.detected_trends:
        print(f"- {trend.name}: {trend.description}")
        
# View report
if state.report_path:
    print(f"Report saved to: {state.report_path}")
```

A command-line script is also provided for easy use:
```bash
python scripts/run_trend_analysis.py --time-frame WEEK --lookback 4 --format markdown
```
