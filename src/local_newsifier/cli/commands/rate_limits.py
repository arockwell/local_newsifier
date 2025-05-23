"""
Rate limiting commands.

This module provides commands for inspecting and managing rate limits:
- Viewing current rate limit usage
- Checking rate limit status for all services
- Resetting rate limits (for testing)
"""

import json

import click
from tabulate import tabulate

from local_newsifier.config.settings import settings
from local_newsifier.utils.rate_limiter import get_rate_limiter


@click.group(name="rate-limits")
def rate_limits_group():
    """Inspect and manage API rate limits."""
    pass


@rate_limits_group.command(name="status")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def rate_limit_status(json_output: bool):
    """Show current rate limit status for all services."""
    limiter = get_rate_limiter()

    # Define all services and their configurations
    services = {
        "apify": {
            "max_calls": settings.RATE_LIMIT_APIFY_CALLS,
            "period": settings.RATE_LIMIT_APIFY_PERIOD,
            "description": "Apify API",
        },
        "rss": {
            "max_calls": settings.RATE_LIMIT_RSS_CALLS,
            "period": settings.RATE_LIMIT_RSS_PERIOD,
            "description": "RSS Feed Fetching",
        },
        "web": {
            "max_calls": settings.RATE_LIMIT_WEB_CALLS,
            "period": settings.RATE_LIMIT_WEB_PERIOD,
            "description": "Web Scraping",
        },
        "openai": {
            "max_calls": settings.RATE_LIMIT_OPENAI_CALLS,
            "period": settings.RATE_LIMIT_OPENAI_PERIOD,
            "description": "OpenAI API",
        },
    }

    # Collect stats for each service
    all_stats = {}
    table_data = []

    for service_name, config in services.items():
        stats = limiter.get_usage_stats(service_name, config["max_calls"], config["period"])

        all_stats[service_name] = stats

        # Format for table display
        table_data.append(
            [
                config["description"],
                f"{stats['available_tokens']}/{stats['max_tokens']}",
                f"{stats['usage_percentage']:.1f}%",
                f"{config['period']}s",
                f"{stats['time_until_refill']:.1f}s",
            ]
        )

    if json_output:
        click.echo(json.dumps(all_stats, indent=2))
    else:
        headers = ["Service", "Available/Max", "Usage %", "Period", "Refill In"]
        click.echo("\nRate Limit Status:")
        click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))
        click.echo(f"\nBackoff enabled: {settings.RATE_LIMIT_ENABLE_BACKOFF}")
        click.echo(f"Max retries: {settings.RATE_LIMIT_MAX_RETRIES}")
        click.echo(f"Initial backoff: {settings.RATE_LIMIT_INITIAL_BACKOFF}s")
        click.echo(f"Backoff multiplier: {settings.RATE_LIMIT_BACKOFF_MULTIPLIER}x")


@rate_limits_group.command(name="check")
@click.argument("service", type=click.Choice(["apify", "rss", "web", "openai"]))
def check_limit(service: str):
    """Check if a specific service has rate limit capacity."""
    limiter = get_rate_limiter()

    # Get service configuration
    configs = {
        "apify": (settings.RATE_LIMIT_APIFY_CALLS, settings.RATE_LIMIT_APIFY_PERIOD),
        "rss": (settings.RATE_LIMIT_RSS_CALLS, settings.RATE_LIMIT_RSS_PERIOD),
        "web": (settings.RATE_LIMIT_WEB_CALLS, settings.RATE_LIMIT_WEB_PERIOD),
        "openai": (settings.RATE_LIMIT_OPENAI_CALLS, settings.RATE_LIMIT_OPENAI_PERIOD),
    }

    max_calls, period = configs[service]
    stats = limiter.get_usage_stats(service, max_calls, period)

    if stats["available_tokens"] > 0:
        click.echo(f"✅ {service} has capacity: {stats['available_tokens']} calls available")
    else:
        click.echo(
            f"❌ {service} is rate limited. Retry in {stats['time_until_refill']:.1f} seconds"
        )


@rate_limits_group.command(name="reset")
@click.argument("service", type=click.Choice(["apify", "rss", "web", "openai", "all"]))
@click.confirmation_option(prompt="Are you sure you want to reset rate limits?")
def reset_limits(service: str):
    """Reset rate limits for a service (for testing only)."""
    limiter = get_rate_limiter()

    services = ["apify", "rss", "web", "openai"] if service == "all" else [service]

    for svc in services:
        key = limiter._get_key(svc)
        limiter._redis.delete(key)
        click.echo(f"✅ Reset rate limits for {svc}")

    click.echo("\nRate limits have been reset.")
