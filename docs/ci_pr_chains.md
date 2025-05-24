# CI Support for PR Chains

Our GitHub Actions workflow supports running tests on PRs that target other PRs (not just main).

This allows you to create PR chains where you build upon work from other open PRs.

## Creating PRs that Target Another PR

1. Create a new branch from the branch of the PR you want to extend.
2. Push your branch and open a PR with the base set to that earlier PR's branch.
3. GitHub will show the chain of PRs and our CI will run tests for each link in the chain.

## Implementation

- Uses `pull_request_target` event with security checks
- Ensures code from the PR is checked out and tested
- Provides the same test feedback as PRs targeting main
- The workflow only runs for `pull_request_target` events when the PR comes from the same repository, preventing untrusted forks from executing the job.
