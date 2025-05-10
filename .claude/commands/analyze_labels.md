You'll analyze issues and PRs to identify label inconsistencies and suggest corrections.

If a label argument is provided (e.g., project:analyze_labels in-progress):
- Focus on issues with that specific label
- Example: project:analyze_labels in-progress (checks all issues with in-progress label)

If no label is provided:
- Analyze all open issues and their labels

Use the gh cli command to analyze issues and their related PRs:

1. List issues based on the provided filter:
   gh issue list --state open --limit 100 [--label LABEL_ARGUMENT]

2. For each issue, check for related PRs:
   gh pr list --search "issue:#ISSUE_NUMBER"

3. Check labels on both issues and PRs:
   gh issue view ISSUE_NUMBER --json labels
   gh pr view PR_NUMBER --json labels

4. Identify the following inconsistencies:
   - Issues with 'in-progress' label but no open PRs
   - Issues with open PRs but missing 'in-progress' label
   - Issues with merged PRs but still open
   - PRs with incorrect labels based on their status

5. Create a report categorized by issue type:
   - LABEL REMOVALS: Issues with 'in-progress' label that should have it removed
   - LABEL ADDITIONS: Issues missing 'in-progress' label that should have it
   - ISSUE CLOSURES: Issues that appear complete and can be closed
   - OTHER INCONSISTENCIES: Any other label problems detected

6. Provide commands to fix each issue:
   - gh issue edit ISSUE_NUMBER --remove-label "in-progress"
   - gh issue edit ISSUE_NUMBER --add-label "in-progress"
   - gh issue close ISSUE_NUMBER --reason "completed"

This helps maintain consistent labeling across issues and PRs, improving project tracking accuracy and reducing manual maintenance.