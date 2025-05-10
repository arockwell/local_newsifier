You'll analyze a specific PR for test failures.

If a PR number is provided as an argument (e.g., project:fix_tests_in 348):
- Focus on that specific PR number
- Use "gh pr view $ARGUMENTS" to look at the specified PR

If no PR number is provided:
- Find your current PR using the gh cli command
- Run "gh pr list --author @me" to find your PRs

You need to use the gh cli command to figure out what went wrong with the tests.

Tests are failing in github. Also, it wouldn't hurt to check the merge status either.

If we have conflicts, definitely alert me.

Otherwise, make a plan for how to fix the tests, and get my approval before proceeding.