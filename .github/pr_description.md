# Description

Adds a local scheduler for automated news fetching and analysis, replacing the previous AWS Lambda-based approach. This makes the project easier to develop and test locally.

# Changes

- Added `src/local_newsifier/scheduler.py` for local scheduling
- Added schedule package to project dependencies
- Removed AWS Lambda and serverless configuration
- Implemented simple local file-based storage
- Added comprehensive logging

# Testing

- Tested locally with both web and RSS sources
- Verified logging and error handling
- Confirmed file output generation
- Tested scheduler interval functionality

# Screenshots/Logs

```
2024-04-13 12:00:00 - scheduler - INFO - Starting scheduler with 60 minute interval
2024-04-13 12:00:00 - scheduler - INFO - Starting news fetch cycle
2024-04-13 12:00:00 - scheduler - INFO - Processing Gainesville Sun (https://www.gainesville.com/news/)
2024-04-13 12:00:05 - scheduler - INFO - Successfully processed Gainesville Sun
2024-04-13 12:00:05 - scheduler - INFO - Processing WUFT News (https://www.wuft.org/news/feed/)
2024-04-13 12:00:08 - scheduler - INFO - Successfully processed WUFT News
2024-04-13 12:00:08 - scheduler - INFO - Completed news fetch cycle
```

# Notes

- This change simplifies the development workflow
- No AWS dependencies required
- Easy to run locally or on any server
- Can be run as a background process
- Future enhancements can focus on analysis features rather than infrastructure

---

# Checklist
* [x] Tests added/updated and passing
* [x] Documentation updated (if needed)
* [x] Code follows project style guidelines
* [x] Verified changes in development environment