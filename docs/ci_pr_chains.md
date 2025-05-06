# CI Support for PR Chains

This document explains how our CI system handles Pull Request (PR) chains in the Local Newsifier project.

## What are PR Chains?

PR chains occur when you create a new PR that targets another PR branch instead of the main branch. This is useful in several scenarios:

1. Building on work that isn't yet merged to main
2. Splitting large changes into multiple, sequential PRs
3. Creating dependent features that build on each other

## How CI Works with PR Chains

Our GitHub Actions workflow has been configured to support testing PRs that target other PRs. Here's how it works:

1. When you create a PR targeting the main branch, tests run as usual
2. When you create a PR targeting another PR branch, tests will also run
3. Test results appear in GitHub as checks on your PR
4. A comment will be posted to the PR with the test results

This ensures that code quality is maintained throughout the PR chain, not just when merging to main.

## Technical Implementation

We use GitHub's `pull_request_target` event to trigger tests on PRs targeting branches other than main. For security reasons, we only allow this for PRs from the same repository.

The workflow:
1. Detects if the PR is targeting main or another branch
2. Checks out the appropriate code
3. Runs the tests
4. Posts the results as a comment on the PR

## Best Practices

When working with PR chains:

1. **Keep PRs focused**: Each PR in the chain should address a specific concern
2. **Maintain test coverage**: Ensure tests pass at each step in the chain
3. **Use clear PR titles**: Include references to parent PRs in the title or description
4. **Merge in order**: Start merging from the first PR in the chain (closest to main)

## Troubleshooting

If tests aren't running on your PR chain:

1. Verify the PR is targeting a branch other than main
2. Check that the PR is from the same repository (not a fork)
3. Look at the GitHub Actions workflow to see if any errors occurred

For more help, reach out to the project maintainers.