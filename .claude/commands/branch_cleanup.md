You'll help manage Git branches by identifying stale branches and suggesting cleanup actions.

If a days threshold is provided (e.g., project:branch_cleanup 30):
- Focus on branches not updated in the specified number of days
- Example: project:branch_cleanup 30 (branches older than 30 days)

If no threshold is provided:
- Default to analyzing branches not updated in the last 14 days

Analyze branches with these steps:

1. List all local branches with their last commit date:
   git for-each-ref --sort=committerdate refs/heads/ --format='%(committerdate:short) %(refname:short)'

2. Identify branches not recently updated based on threshold:
   git for-each-ref --sort=committerdate refs/heads/ --format='%(committerdate:short) %(refname:short)' | awk -v threshold="$(date -d 'now-{days} days' '+%Y-%m-%d')" '$1 < threshold'

3. Find branches already merged to main:
   git branch --merged main

4. Show branches with closed PRs that haven't been deleted:
   for branch in $(git branch | cut -c 3-); do if [ "$branch" != "main" ]; then pr_state=$(gh pr list --head $branch --state all --json state | jq -r '.[0].state // "none"'); if [ "$pr_state" = "MERGED" ] || [ "$pr_state" = "CLOSED" ]; then echo "$branch (PR status: $pr_state)"; fi; fi; done

5. Categorize branches for action:
   - Safe to delete: Fully merged branches with closed/merged PRs
   - Review before deletion: Stale branches with closed PRs that have some unmerged commits
   - Keep: Active branches, branches with open PRs

6. Provide commands to safely delete branches:
   For each branch safe to delete:
   git branch -d {branch_name}   # Safe delete (only if merged)
   
   For branches requiring review:
   git diff main..{branch_name}  # Review unmerged changes
   git branch -D {branch_name}   # Force delete (after review)

7. Suggest creating backup references before deletion:
   git tag backup/{branch_name} {branch_name}  # Create backup tag
   
8. Summarize branch status:
   - Total branches analyzed
   - Number recommended for deletion
   - Number requiring review
   - Number to keep

This systematic analysis helps maintain a clean repository by identifying and safely removing stale branches.