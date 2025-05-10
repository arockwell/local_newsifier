You'll analyze recently merged PRs to find issues that are still open but have been implemented.

If a timeframe argument is provided (e.g., project:analyze_closed_prs 30d):
- Focus on PRs merged within that timeframe (e.g., last 30 days)
- Accepted formats: 7d (days), 2w (weeks), 1m (months)

If no timeframe is provided:
- Default to analyzing PRs merged in the last 14 days

Use the gh cli command to find and analyze merged PRs:

1. List recently merged PRs
   gh pr list --state merged --limit 50

2. For each PR, look at the title and body for issue references:
   gh pr view PR_NUMBER

3. Check if the referenced issues are still open:
   gh issue view ISSUE_NUMBER

4. Group the results by confidence level:
   - HIGH: Issues mentioned with "fixes #X", "closes #X" in PR title
   - MEDIUM: Issues mentioned in PR body with implementation details
   - LOW: Issues simply referenced in PR

5. Create a report showing:
   - Issues that can likely be closed (high confidence)
   - Issues that need review before closing (medium confidence)
   - Issues that need verification (low confidence)

6. Provide commands to easily close issues if appropriate:
   gh issue close ISSUE_NUMBER --reason "completed"

This helps maintain a cleaner issue tracker by identifying issues that have been implemented but not formally closed.