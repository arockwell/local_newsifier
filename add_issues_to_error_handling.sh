#\!/bin/bash
# Add Error Handling issues
PROJECT_ID="PVT_kwHNVCzOAOC8og"
ISSUES=(171 170 169 118 80 79 78 77 75 74)

for ISSUE_NUM in "${ISSUES[@]}"; do
  echo "Adding issue #$ISSUE_NUM to Error Handling Framework project"
  gh issue edit "$ISSUE_NUM" --add-project "$PROJECT_ID"
done
