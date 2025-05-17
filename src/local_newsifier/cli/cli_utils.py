"""Helper utilities for CLI commands."""

from typing import Any, Callable

import click
from tabulate import tabulate
from fastapi_injectable import get_injected_obj


def load_dependency(provider: Callable[..., Any]) -> Any:
    """Load a dependency using fastapi-injectable."""
    return get_injected_obj(provider)


def print_table(headers, rows) -> None:
    """Print a table using ``tabulate`` with the project's default format."""
    click.echo(tabulate(rows, headers=headers, tablefmt="simple"))

