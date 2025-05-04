"""
Configuration management commands.

This module provides commands for managing CLI configuration, including:
- Managing environments (dev, staging, production)
- Setting configuration values
- Viewing configuration settings
"""

import json

import click
from tabulate import tabulate

from local_newsifier.cli.config import get_config


@click.group(name="config")
def config_group():
    """Manage CLI configuration."""
    pass


@config_group.command(name="list-env")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def list_environments(json_output):
    """List available environments."""
    config = get_config()
    env_names = config.get_env_names()
    current_env = config.get_current_env()

    if json_output:
        result = {
            "current": current_env,
            "environments": [
                {
                    "name": env,
                    "is_current": env == current_env,
                    "config": config.format_config_for_display(env),
                }
                for env in env_names
            ],
        }
        click.echo(json.dumps(result, indent=2))
        return

    # Format data for table
    table_data = []
    for env_name in env_names:
        env_config = config.get_env_config(env_name)
        table_data.append(
            [
                "* " if env_name == current_env else "",
                env_name,
                env_config.get("name", ""),
                "Yes" if "DATABASE_URL" in env_config else "No",
                "Yes" if "APIFY_TOKEN" in env_config else "No",
            ]
        )

    # Display table
    headers = ["", "Environment", "Name", "Database", "Apify"]
    click.echo("Available Environments:")
    click.echo(tabulate(table_data, headers=headers, tablefmt="simple"))
    click.echo(f"\nCurrent environment: {current_env}")


@config_group.command(name="show-env")
@click.argument("env_name", required=False)
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.option("--show-secrets", is_flag=True, help="Show sensitive information")
def show_environment(env_name, json_output, show_secrets):
    """Show environment details."""
    config = get_config()

    # If no environment name is provided, use current
    if not env_name:
        env_name = config.get_current_env()

    # Check if environment exists
    if env_name not in config.get_env_names():
        click.echo(
            click.style(f"Error: Environment '{env_name}' not found", fg="red"),
            err=True,
        )
        return

    # Get configuration
    env_config = config.format_config_for_display(
        env_name, mask_secrets=not show_secrets
    )

    if json_output:
        result = {"name": env_name, "config": env_config}
        click.echo(json.dumps(result, indent=2))
        return

    # Display configuration
    current_marker = "* " if env_name == config.get_current_env() else ""
    display_name = env_config.get("name", env_name)
    click.echo(
        click.style(
            f"{current_marker}Environment: {env_name} ({display_name})",
            fg="green",
            bold=True,
        )
    )

    # Display settings
    if not env_config:
        click.echo("No configuration values set")
        return

    table_data = []
    for key, value in env_config.items():
        if key == "name":
            continue
        table_data.append([key, value])

    click.echo("\nConfiguration:")
    click.echo(tabulate(table_data, headers=["Key", "Value"], tablefmt="simple"))


@config_group.command(name="set-env")
@click.argument("env_name", required=True)
def set_environment(env_name):
    """Set the current environment."""
    config = get_config()

    # Check if environment exists
    if env_name not in config.get_env_names():
        click.echo(
            click.style(f"Error: Environment '{env_name}' not found", fg="red"),
            err=True,
        )
        return

    if config.set_current_env(env_name):
        click.echo(f"Current environment set to: {env_name}")
    else:
        click.echo(click.style("Error setting current environment", fg="red"), err=True)


@config_group.command(name="create-env")
@click.argument("env_name", required=True)
@click.option("--name", help="Human-readable name for the environment")
@click.option("--database-url", help="Database connection URL")
@click.option("--api-url", help="API server URL")
@click.option("--apify-token", help="Apify API token")
@click.option("--redis-url", help="Redis connection URL (for Celery)")
@click.option("--log-level", help="Logging level (DEBUG, INFO, WARNING, ERROR)")
@click.option("--set-current", is_flag=True, help="Set this as the current environment")
@click.option("--is-production", is_flag=True, help="Mark as production environment")
def create_environment(
    env_name,
    name,
    database_url,
    api_url,
    apify_token,
    redis_url,
    log_level,
    set_current,
    is_production,
):
    """Create a new environment configuration."""
    config = get_config()

    # Check if environment already exists
    if env_name in config.get_env_names():
        click.echo(
            click.style(f"Error: Environment '{env_name}' already exists", fg="red"),
            err=True,
        )
        return

    # Prepare configuration data
    config_data = {}
    if name:
        config_data["name"] = name
    else:
        config_data["name"] = env_name.capitalize()

    # Add settings if provided
    if database_url:
        config_data["DATABASE_URL"] = database_url
    if api_url:
        config_data["API_URL"] = api_url
    if apify_token:
        config_data["APIFY_TOKEN"] = apify_token
    if redis_url:
        config_data["REDIS_URL"] = redis_url
    if log_level:
        config_data["LOG_LEVEL"] = log_level
    if is_production:
        config_data["is_production"] = "true"

    # Create environment
    if config.create_env(env_name, config_data):
        click.echo(f"Environment '{env_name}' created successfully")

        # Set as current if requested
        if set_current:
            config.set_current_env(env_name)
            click.echo(f"Current environment set to: {env_name}")
    else:
        click.echo(
            click.style(f"Error creating environment '{env_name}'", fg="red"), err=True
        )


@config_group.command(name="update-env")
@click.argument("env_name", required=True)
@click.option("--name", help="Human-readable name for the environment")
@click.option("--database-url", help="Database connection URL")
@click.option("--api-url", help="API server URL")
@click.option("--apify-token", help="Apify API token")
@click.option("--redis-url", help="Redis connection URL (for Celery)")
@click.option("--log-level", help="Logging level (DEBUG, INFO, WARNING, ERROR)")
@click.option(
    "--is-production/--not-production",
    help="Mark as production/non-production environment",
)
def update_environment(
    env_name,
    name,
    database_url,
    api_url,
    apify_token,
    redis_url,
    log_level,
    is_production,
):
    """Update an existing environment configuration."""
    config = get_config()

    # Check if environment exists
    if env_name not in config.get_env_names():
        click.echo(
            click.style(f"Error: Environment '{env_name}' not found", fg="red"),
            err=True,
        )
        return

    # Check if at least one option was provided
    if not any(
        [
            name is not None,
            database_url is not None,
            api_url is not None,
            apify_token is not None,
            redis_url is not None,
            log_level is not None,
            is_production is not None,
        ]
    ):
        click.echo("Error: No update parameters provided")
        return

    # Prepare configuration data
    config_data = {}
    if name is not None:
        config_data["name"] = name
    if database_url is not None:
        config_data["DATABASE_URL"] = database_url
    if api_url is not None:
        config_data["API_URL"] = api_url
    if apify_token is not None:
        config_data["APIFY_TOKEN"] = apify_token
    if redis_url is not None:
        config_data["REDIS_URL"] = redis_url
    if log_level is not None:
        config_data["LOG_LEVEL"] = log_level
    if is_production is not None:
        config_data["is_production"] = "true" if is_production else "false"

    # Update environment
    if config.update_env(env_name, config_data):
        click.echo(f"Environment '{env_name}' updated successfully")
    else:
        click.echo(
            click.style(f"Error updating environment '{env_name}'", fg="red"), err=True
        )


@config_group.command(name="delete-env")
@click.argument("env_name", required=True)
@click.option("--force", is_flag=True, help="Skip confirmation")
def delete_environment(env_name, force):
    """Delete an environment configuration."""
    config = get_config()

    # Check if environment exists
    if env_name not in config.get_env_names():
        click.echo(
            click.style(f"Error: Environment '{env_name}' not found", fg="red"),
            err=True,
        )
        return

    # Check if it's the default environment
    if env_name == "dev":
        click.echo(
            click.style("Error: Cannot delete the default environment", fg="red"),
            err=True,
        )
        return

    # Confirm deletion
    if not force:
        if not click.confirm(
            f"Are you sure you want to delete environment '{env_name}'?"
        ):
            click.echo("Operation canceled.")
            return

    # Delete environment
    if config.delete_env(env_name):
        click.echo(f"Environment '{env_name}' deleted successfully")
    else:
        click.echo(
            click.style(f"Error deleting environment '{env_name}'", fg="red"), err=True
        )


@config_group.command(name="import")
@click.argument("file_path", type=click.Path(exists=True), required=True)
@click.option("--force", is_flag=True, help="Overwrite existing environments")
def import_config(file_path, force):
    """Import environment configurations from a file."""
    config = get_config()

    try:
        # Load configurations from file
        with open(file_path, "r") as f:
            import_data = json.load(f)

        if not isinstance(import_data, dict):
            click.echo(
                click.style("Error: Invalid import file format", fg="red"), err=True
            )
            return

        imported_count = 0
        for env_name, env_config in import_data.items():
            # Skip if not a dictionary or a reserved section
            if not isinstance(env_config, dict) or env_name in ["global"]:
                continue

            # Check if environment already exists
            if env_name in config.get_env_names() and not force:
                click.echo(f"Skipping existing environment: {env_name}")
                continue

            # Create or update environment
            if env_name in config.get_env_names():
                config.update_env(env_name, env_config)
                click.echo(f"Updated environment: {env_name}")
            else:
                config.create_env(env_name, env_config)
                click.echo(f"Created environment: {env_name}")

            imported_count += 1

        click.echo(f"Import completed: {imported_count} environments processed")

    except json.JSONDecodeError:
        click.echo(
            click.style(f"Error: Invalid JSON format in {file_path}", fg="red"),
            err=True,
        )
    except Exception as e:
        click.echo(click.style(f"Error importing config: {str(e)}", fg="red"), err=True)


@config_group.command(name="export")
@click.argument("file_path", type=click.Path(), required=True)
@click.option(
    "--include-all",
    is_flag=True,
    help="Include all environments (default: current only)",
)
@click.option("--mask-secrets", is_flag=True, help="Mask sensitive information")
def export_config(file_path, include_all, mask_secrets):
    """Export environment configurations to a file."""
    config = get_config()

    try:
        # Prepare export data
        export_data = {}

        if include_all:
            # Export all environments
            for env_name in config.get_env_names():
                export_data[env_name] = config.format_config_for_display(
                    env_name, mask_secrets=mask_secrets
                )
        else:
            # Export only current environment
            current_env = config.get_current_env()
            export_data[current_env] = config.format_config_for_display(
                current_env, mask_secrets=mask_secrets
            )

        # Write to file
        with open(file_path, "w") as f:
            json.dump(export_data, f, indent=2)

        click.echo(f"Configuration exported to: {file_path}")

    except Exception as e:
        click.echo(click.style(f"Error exporting config: {str(e)}", fg="red"), err=True)
