# Fix Railway Deployment Configuration

## Description

This PR removes the redundant `pip install -e .` command from the Railway deployment configuration. This command is unnecessary because:

1. Nixpacks (the specified builder) already automatically installs dependencies from requirements.txt during the build phase
2. The `-e` flag installs the package in "editable" mode, which is primarily intended for development, not production deployments
3. Previous working configurations documented in our memory bank didn't include this command

## Changes

- Modified `railway.json` to remove the `pip install -e .` command from the start command

## Testing

This change should simplify the deployment process and follow Railway's recommended practices.

## Additional Notes

The requirements.txt file already contains all necessary dependencies, and the pyproject.toml handles the package structure, so the explicit installation step is redundant.
