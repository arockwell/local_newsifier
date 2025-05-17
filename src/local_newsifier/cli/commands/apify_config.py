"""
Apify source configuration management commands.

This module provides commands for managing Apify source configurations, including:
- Listing configurations
- Adding new configurations
- Showing configuration details
- Removing configurations
- Updating configuration properties
"""

import json
import click
from datetime import datetime

from local_newsifier.cli.cli_utils import load_dependency, print_table

from local_newsifier.di.providers import get_apify_source_config_service


@click.group(name="apify-config")
def apify_config_group():
    """Manage Apify source configurations."""
    pass


@apify_config_group.command(name="list")
@click.option("--active-only", is_flag=True, help="Show only active configurations")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.option("--limit", type=int, default=100, help="Maximum number of configurations to display")
@click.option("--skip", type=int, default=0, help="Number of configurations to skip")
@click.option("--source-type", help="Filter by source type (e.g., news, blog)")
def list_configs(active_only, json_output, limit, skip, source_type):
    """List all Apify source configurations with optional filtering."""
    # Get the service using the injectable provider
    apify_source_config_service = load_dependency(get_apify_source_config_service)
    
    # Get configs based on filters
    configs_dict = apify_source_config_service.list_configs(
        skip=skip, 
        limit=limit, 
        active_only=active_only, 
        source_type=source_type
    )
    
    if json_output:
        click.echo(json.dumps(configs_dict, indent=2, default=str))
        return
    
    if not configs_dict:
        click.echo("No Apify source configurations found.")
        return
    
    # Format data for table
    table_data = []
    for config in configs_dict:
        last_run = config.get("last_run_at")
        if last_run:
            # Handle both datetime and string representations
            if isinstance(last_run, str):
                try:
                    last_run = datetime.fromisoformat(last_run).strftime("%Y-%m-%d %H:%M")
                except:
                    # Handle potential format issues
                    pass
        
        # Truncate input_configuration if it's too long
        input_config = str(config.get("input_configuration", {}))
        if len(input_config) > 30:
            input_config = input_config[:27] + "..."
        
        table_data.append([
            config["id"],
            config["name"],
            config["actor_id"],
            config["source_type"],
            "✓" if config["is_active"] else "✗",
            last_run or "Never",
            input_config
        ])
    
    # Display table
    headers = ["ID", "Name", "Actor ID", "Type", "Active", "Last Run", "Config"]
    print_table(headers, table_data)


@apify_config_group.command(name="add")
@click.option("--name", required=True, help="Configuration name")
@click.option("--actor-id", required=True, help="Apify actor ID")
@click.option("--source-type", required=True, help="Source type (e.g., news, blog)")
@click.option("--source-url", help="Source URL (optional)")
@click.option("--schedule", help="Cron schedule expression (optional)")
@click.option("--input", "-i", help="JSON string or file path for actor input configuration")
def add_config(name, actor_id, source_type, source_url, schedule, input):
    """Add a new Apify source configuration."""
    # Get the service using the injectable provider
    apify_source_config_service = load_dependency(get_apify_source_config_service)
    
    # Parse input configuration if provided
    input_configuration = None
    if input:
        if input.startswith("{") or input.startswith("["):
            try:
                input_configuration = json.loads(input)
            except json.JSONDecodeError:
                click.echo(click.style("Error: Input must be valid JSON", fg="red"), err=True)
                return
        elif input.endswith(".json") and input.find("/") != -1:
            # Looks like a file path
            try:
                with open(input, "r") as f:
                    input_configuration = json.load(f)
                click.echo(f"Loaded input configuration from file: {input}")
            except Exception as e:
                click.echo(
                    click.style(f"Error loading input file: {str(e)}", fg="red"),
                    err=True,
                )
                return
    
    try:
        config = apify_source_config_service.create_config(
            name=name,
            actor_id=actor_id,
            source_type=source_type,
            source_url=source_url,
            schedule=schedule,
            input_configuration=input_configuration
        )
        
        click.echo(f"Apify source configuration added successfully with ID: {config['id']}")
        click.echo(f"Name: {config['name']}")
        click.echo(f"Actor ID: {config['actor_id']}")
        click.echo(f"Source Type: {config['source_type']}")
    except Exception as e:
        click.echo(click.style(f"Error adding configuration: {str(e)}", fg="red"), err=True)


@apify_config_group.command(name="show")
@click.argument("id", type=int, required=True)
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def show_config(id, json_output):
    """Show Apify source configuration details."""
    # Get the service using the injectable provider
    apify_source_config_service = load_dependency(get_apify_source_config_service)
    
    try:
        config = apify_source_config_service.get_config(id)
        if not config:
            click.echo(click.style(f"Error: Configuration with ID {id} not found", fg="red"), err=True)
            return
        
        if json_output:
            click.echo(json.dumps(config, indent=2, default=str))
            return
        
        # Display config details
        click.echo(click.style(f"Configuration #{config['id']}: {config['name']}", fg="green", bold=True))
        click.echo(f"Actor ID: {config['actor_id']}")
        click.echo(f"Source Type: {config['source_type']}")
        if config['source_url']:
            click.echo(f"Source URL: {config['source_url']}")
        click.echo(f"Active: {'Yes' if config['is_active'] else 'No'}")
        
        if config['schedule']:
            click.echo(f"Schedule: {config['schedule']}")
        
        last_run = config['last_run_at']
        if last_run:
            click.echo(f"Last Run: {last_run}")
        else:
            click.echo("Last Run: Never")
        
        click.echo("\nInput Configuration:")
        click.echo(json.dumps(config['input_configuration'], indent=2))
        
        created_at = config['created_at']
        click.echo(f"\nCreated At: {created_at}")
    except Exception as e:
        click.echo(click.style(f"Error retrieving configuration: {str(e)}", fg="red"), err=True)


@apify_config_group.command(name="remove")
@click.argument("id", type=int, required=True)
@click.option("--force", is_flag=True, help="Skip confirmation")
def remove_config(id, force):
    """Remove an Apify source configuration."""
    # Get the service using the injectable provider
    apify_source_config_service = load_dependency(get_apify_source_config_service)
    
    try:
        config = apify_source_config_service.get_config(id)
        if not config:
            click.echo(click.style(f"Error: Configuration with ID {id} not found", fg="red"), err=True)
            return
        
        if not force:
            if not click.confirm(f"Are you sure you want to remove configuration '{config['name']}' (ID: {id})?"):
                click.echo("Operation canceled.")
                return
        
        result = apify_source_config_service.remove_config(id)
        if result:
            click.echo(f"Configuration '{config['name']}' (ID: {id}) removed successfully.")
        else:
            click.echo(click.style(f"Error removing configuration with ID {id}", fg="red"), err=True)
    except Exception as e:
        click.echo(click.style(f"Error removing configuration: {str(e)}", fg="red"), err=True)


@apify_config_group.command(name="update")
@click.argument("id", type=int, required=True)
@click.option("--name", help="New configuration name")
@click.option("--actor-id", help="New actor ID")
@click.option("--source-type", help="New source type")
@click.option("--source-url", help="New source URL")
@click.option("--schedule", help="New schedule expression")
@click.option("--active/--inactive", help="Set configuration active or inactive")
@click.option("--input", "-i", help="JSON string or file path for actor input configuration")
def update_config(id, name, actor_id, source_type, source_url, schedule, active, input):
    """Update Apify source configuration properties."""
    # Get the service using the injectable provider
    apify_source_config_service = load_dependency(get_apify_source_config_service)
    
    try:
        # Check if at least one property to update was provided
        if all(v is None for v in [name, actor_id, source_type, source_url, schedule, active, input]):
            click.echo("No properties specified for update. Use --name, --actor-id, etc.")
            return
        
        # Parse input configuration if provided
        input_configuration = None
        if input:
            if input.startswith("{") or input.startswith("["):
                try:
                    input_configuration = json.loads(input)
                except json.JSONDecodeError:
                    click.echo(click.style("Error: Input must be valid JSON", fg="red"), err=True)
                    return
            elif input.endswith(".json") and input.find("/") != -1:
                # Looks like a file path
                try:
                    with open(input, "r") as f:
                        input_configuration = json.load(f)
                    click.echo(f"Loaded input configuration from file: {input}")
                except Exception as e:
                    click.echo(
                        click.style(f"Error loading input file: {str(e)}", fg="red"),
                        err=True,
                    )
                    return
        
        # Update config
        updated_config = apify_source_config_service.update_config(
            config_id=id,
            name=name,
            actor_id=actor_id,
            source_type=source_type,
            source_url=source_url,
            schedule=schedule,
            is_active=active,
            input_configuration=input_configuration
        )
        
        if not updated_config:
            click.echo(click.style(f"Error: Configuration with ID {id} not found", fg="red"), err=True)
            return
            
        click.echo(f"Configuration '{updated_config['name']}' (ID: {id}) updated successfully.")
    except Exception as e:
        click.echo(click.style(f"Error updating configuration: {str(e)}", fg="red"), err=True)


@apify_config_group.command(name="run")
@click.argument("id", type=int, required=True)
@click.option("--output", "-o", help="Save output to file")
def run_config(id, output):
    """Run an Apify actor based on a source configuration.
    
    This command will execute the Apify actor associated with the configuration
    using the stored input parameters.
    
    ID is the ID of the configuration to run.
    
    Examples:
        nf apify-config run 1
        nf apify-config run 2 --output result.json
    """
    # Get the service using the injectable provider
    apify_source_config_service = load_dependency(get_apify_source_config_service)
    
    try:
        # Run the configuration
        result = apify_source_config_service.run_configuration(id)
        
        if result["status"] == "success":
            click.echo(click.style("✓ Actor run completed successfully!", fg="green"))
            click.echo(f"Configuration: {result['config_name']} (ID: {result['config_id']})")
            click.echo(f"Actor ID: {result['actor_id']}")
            click.echo(f"Run ID: {result['run_id']}")
            
            # Output dataset info if available
            if "dataset_id" in result and result["dataset_id"]:
                click.echo(f"Dataset ID: {result['dataset_id']}")
                click.echo(f"To retrieve the data: nf apify get-dataset {result['dataset_id']}")
            
            # Save or display the results
            if output:
                with open(output, "w") as f:
                    json.dump(result, f, indent=2)
                click.echo(f"Output saved to {output}")
        else:
            click.echo(click.style("✗ Actor run failed.", fg="red"), err=True)
            click.echo(click.style(f"Error: {result.get('message', 'Unknown error')}", fg="red"), err=True)
            
    except Exception as e:
        click.echo(click.style(f"Error running configuration: {str(e)}", fg="red"), err=True)