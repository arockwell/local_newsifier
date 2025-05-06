#\!/bin/bash
PROJECT_NAME="Apify Integration Repository"
ISSUES=(217 216 215 214 129 118 116 114 113 112 111 110)

for ISSUE_NUM in "${ISSUES[@]}"; do
  echo "Adding issue #$ISSUE_NUM to $PROJECT_NAME"
  gh issue edit "$ISSUE_NUM" --add-project "$PROJECT_NAME"
done
