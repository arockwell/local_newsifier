#\!/bin/bash
# Add Core Infrastructure issues
PROJECT_ID="PVT_kwHNVCzOAOC8pQ"
ISSUES=(58 61 70 71 73 115 176 183 184 185)

for ISSUE_NUM in "${ISSUES[@]}"; do
  echo "Adding issue #$ISSUE_NUM to Core Infrastructure project"
  gh issue edit "$ISSUE_NUM" --add-project "$PROJECT_ID"
done
