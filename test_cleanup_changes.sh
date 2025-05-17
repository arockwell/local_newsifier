#!/bin/bash
# Script to test the DI cleanup changes without applying them permanently
# Created by Claude on 2025-05-16

# List files to be deleted completely
echo "Files that will be deleted:"
echo "- tests/test_fastapi_injectable_adapter.py"
echo "- tests/services/test_mock_rss_feed_service.py"
echo

# Count container references in source code
echo "Current container references in source code:"
echo "$(grep -r "self.container" src/local_newsifier --include="*.py" | wc -l) references to 'self.container'"
echo "$(grep -r "container=None" src/local_newsifier --include="*.py" | wc -l) instances of 'container=None' parameter"
echo "$(grep -r "_ensure_dependencies" src/local_newsifier --include="*.py" | wc -l) references to '_ensure_dependencies'"
echo "$(grep -r "from local_newsifier.container import" src/local_newsifier --include="*.py" | wc -l) imports of 'container'"
echo

# Count container references in tests
echo "Current container references in tests:"
echo "$(grep -r "mock_container" tests --include="*.py" | wc -l) references to 'mock_container'"
echo "$(grep -r "create_test_container" tests --include="*.py" | wc -l) references to 'create_test_container'"
echo

# Preview changes to specific files
echo "Preview of cleanup for entity_tracker_service.py:"
sed -n '/def _ensure_dependencies/,/^    def /p' src/local_newsifier/tools/entity_tracker_service.py

echo
echo "Preview of parameter cleanup for apify_source_config_service.py:"
grep -A5 "__init__" src/local_newsifier/services/apify_source_config_service.py

echo
echo "Note: This script only shows what changes would be made. Run cleanup_legacy_di.sh to apply them."