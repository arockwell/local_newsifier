# CI Support for PR Chains

Our GitHub Actions workflow supports running tests on PRs that target other PRs (not just main).

This allows you to create PR chains where you build upon work from other open PRs.

## Implementation

- Uses `pull_request_target` event with security checks
- Ensures code from the PR is checked out and tested
- Provides the same test feedback as PRs targeting main
