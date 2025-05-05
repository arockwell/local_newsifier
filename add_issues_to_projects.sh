#\!/bin/bash
PROJECT_ID="PVT_kwHNVCzOAOC8nQ"
ISSUES=(218 217 216 215 214 129 118 116 114 113 112 111 110)

for ISSUE_NUM in "${ISSUES[@]}"; do
  echo "Adding issue #$ISSUE_NUM to Apify Integration project"
  gh issue edit "$ISSUE_NUM" --add-project "$PROJECT_ID"
done
