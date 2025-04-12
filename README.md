# Project Chronicle Persistence

A robust system for fetching, analyzing, and storing local news articles from Gainesville, FL using crew.ai Flows.

## Project Overview

This system automatically fetches local news articles, performs Named Entity Recognition (NER) analysis, and stores the results with a focus on reliability and observability.

## Features

- Automated news article fetching
- Named Entity Recognition (NER) analysis
- Robust error handling and retry mechanisms
- State persistence and workflow resumption
- Comprehensive logging and monitoring

## Setup

1. Install Poetry (package manager):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Install dependencies:
```bash
poetry install
```

3. Download spaCy model:
```bash
poetry run python -m spacy download en_core_web_lg
```

## Usage

Run the pipeline:
```bash
poetry run python scripts/run_pipeline.py --url <URL>
```

## Development

Run tests:
```bash
poetry run pytest
```

## Project Structure

```
src/
├── local_newsifier/
│   ├── tools/          # Tool implementations
│   ├── models/         # Pydantic models
│   ├── flows/          # crew.ai Flow definitions
│   └── config/         # Configuration
tests/                  # Test suite
scripts/                # Runtime scripts
```

## Configuration

The system can be configured through:
- Environment variables
- Configuration files in `src/local_newsifier/config/`

## Error Handling

The system implements comprehensive error handling:
- Network errors
- Parsing failures
- Processing errors
- State management issues

## State Management

Uses crew.ai's SQLite checkpointer for:
- Workflow state persistence
- Progress tracking
- Error recovery
- Flow resumption

## Monitoring

- Comprehensive logging
- State tracking
- Error reporting
- Progress monitoring

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT 