#!/bin/bash

# This script analyzes files containing mock_container references and generates a report
# Run from the project root directory

echo "Analyzing files with mock_container references..."
echo "================================================"

TESTS_DIR="tests"
OUTPUT_FILE="mock_container_report.md"

# Create the report file
echo "# Mock Container Cleanup Report" > "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "This report lists files that still have references to the legacy 'mock_container' fixture." >> "$OUTPUT_FILE"
echo "These files need to be updated to use the injectable pattern." >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Find all Python files containing "mock_container"
grep -l "mock_container" $(find $TESTS_DIR -name "*.py") | while read file; do
    # Count references
    references=$(grep -c "mock_container" "$file")
    
    # Check if the file is already skipped
    skipped=$(grep -c "pytest.mark.skip" "$file")
    
    echo "## File: $file" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    
    if [ "$skipped" -gt 0 ]; then
        echo "- Status: **SKIPPED** (has pytest.mark.skip)" >> "$OUTPUT_FILE"
    else
        echo "- Status: **ACTIVE** (needs updating)" >> "$OUTPUT_FILE"
    fi
    
    echo "- References to mock_container: $references" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    
    # Extract test methods using mock_container
    echo "### Test methods using mock_container:" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo '```python' >> "$OUTPUT_FILE"
    grep -B 1 -A 1 "mock_container" "$file" >> "$OUTPUT_FILE"
    echo '```' >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
done

echo "Report generated: $OUTPUT_FILE"
echo "Files to update: $(grep -l "mock_container" $(grep -L "pytest.mark.skip" $(find $TESTS_DIR -name "*.py")) | wc -l)"