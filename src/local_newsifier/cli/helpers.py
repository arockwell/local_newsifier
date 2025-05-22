import json
import logging
import os
from typing import Any, Optional

import click

from local_newsifier.config.settings import settings


def ensure_apify_token(token: Optional[str] = None) -> bool:
    """Ensure the Apify token is available.

    If ``token`` is provided it overrides environment or settings. In test mode a
    dummy token is injected when missing.

    Returns:
        bool: ``True`` if a token is available, ``False`` otherwise.
    """
    if token:
        settings.APIFY_TOKEN = token
        return True

    # Provide a default token when running tests
    if os.environ.get("PYTEST_CURRENT_TEST") is not None:
        if not settings.APIFY_TOKEN:
            logging.warning("Running CLI in test mode with dummy APIFY_TOKEN")
            settings.APIFY_TOKEN = "test_dummy_token"
        return True

    env_token = os.environ.get("APIFY_TOKEN")
    if env_token:
        settings.APIFY_TOKEN = env_token
        return True

    if settings.APIFY_TOKEN:
        return True

    click.echo(click.style("Error: APIFY_TOKEN is not set.", fg="red"), err=True)
    click.echo("Please set it using one of these methods:")
    click.echo("  1. Export as environment variable: export APIFY_TOKEN=your_token")
    click.echo("  2. Add to .env file: APIFY_TOKEN=your_token")
    click.echo("  3. Use --token option with this command")
    return False


def write_output(data: Any, path: Optional[str] = None) -> None:
    """Write JSON output to a file or echo to the console."""
    if path:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        click.echo(f"Output saved to {path}")
    else:
        click.echo(json.dumps(data, indent=2))
