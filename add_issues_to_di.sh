#\!/bin/bash
# Add DI issues
PROJECT_ID="PVT_kwHNVCzOAOC8oA"
ISSUES=(200 143 119 122 141 151 202 203 204 205 206 207 208 211 212)

for ISSUE_NUM in "${ISSUES[@]}"; do
  echo "Adding issue #$ISSUE_NUM to Dependency Injection Refactoring project"
  gh issue edit "$ISSUE_NUM" --add-project "$PROJECT_ID"
done
