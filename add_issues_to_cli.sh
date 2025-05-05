#\!/bin/bash
# Add CLI issues
PROJECT_ID="PVT_kwHNVCzOAOC8pA"
ISSUES=(210 209 194 82 215)

for ISSUE_NUM in "${ISSUES[@]}"; do
  echo "Adding issue #$ISSUE_NUM to CLI Improvements project"
  gh issue edit "$ISSUE_NUM" --add-project "$PROJECT_ID"
done
