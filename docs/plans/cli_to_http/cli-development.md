# CLI Development Knowledge Base

## Overview
This document consolidates all knowledge about CLI development patterns, best practices, and implementation strategies for the Local Newsifier command-line interface.

## Architecture

### Command Structure
```
nf (main command)
├── feeds          # RSS feed management
│   ├── list
│   ├── add
│   ├── show
│   ├── update
│   ├── remove
│   └── process
├── db             # Database operations
│   ├── stats
│   ├── duplicates
│   ├── articles
│   ├── inspect
│   └── verify
├── apify          # Apify integration
│   ├── test
│   ├── scrape-content
│   ├── web-scraper
│   ├── run-actor
│   ├── config
│   └── sync-schedules
└── analyze        # Analysis operations
    ├── entity
    ├── sentiment
    └── trends
```

### Command Implementation Pattern
```python
# Standard command structure
@cli.command()
@click.option('--format', type=click.Choice(['json', 'table']), default='table')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def command_name(
    ctx: click.Context,
    format: str,
    verbose: bool,
    # Injected dependencies
    service: Annotated[ServiceType, Depends(get_service)]
):
    """Command description for help text."""
    try:
        # Validate inputs
        if not validate_input():
            raise click.BadParameter("Invalid input")

        # Execute operation
        result = service.operation()

        # Format output
        formatter = get_formatter(format)
        output = formatter.format(result)

        # Display result
        click.echo(output)

    except ServiceError as e:
        ctx.obj['logger'].error(f"Operation failed: {e}")
        raise click.ClickException(str(e))
```

## Dependency Injection in CLI

### Using Provider Functions
```python
# In cli/commands/feeds.py
from typing import Annotated
from fastapi import Depends
from local_newsifier.di.providers import get_feed_service

@feeds_cli.command()
def list(
    ctx: click.Context,
    service: Annotated[FeedService, Depends(get_feed_service)]
):
    """List all RSS feeds."""
    feeds = service.get_all()
    # ... rest of implementation
```

### Testing CLI Commands
```python
# In tests/cli/test_feeds.py
def test_feeds_list(cli_runner, mock_feed_service):
    # Mock the provider
    with patch('local_newsifier.di.providers.get_feed_service',
               return_value=mock_feed_service):
        # Mock service response
        mock_feed_service.get_all.return_value = [
            Feed(id=1, url="https://example.com/rss", name="Example")
        ]

        # Run command
        result = cli_runner.invoke(cli, ['feeds', 'list'])

        # Verify
        assert result.exit_code == 0
        assert "Example" in result.output
```

## Output Formatting

### Formatter Pattern
```python
# Base formatter interface
class OutputFormatter(ABC):
    @abstractmethod
    def format(self, data: Any) -> str:
        pass

# Table formatter
class TableFormatter(OutputFormatter):
    def format(self, data: List[dict]) -> str:
        if not data:
            return "No data found."

        table = Table()

        # Add columns from first row
        for key in data[0].keys():
            table.add_column(key.title())

        # Add rows
        for row in data:
            table.add_row(*[str(v) for v in row.values()])

        # Convert to string
        console = Console()
        with console.capture() as capture:
            console.print(table)

        return capture.get()

# JSON formatter
class JSONFormatter(OutputFormatter):
    def format(self, data: Any) -> str:
        return json.dumps(data, indent=2, default=str)

# Machine-readable formatter
class MachineFormatter(OutputFormatter):
    def format(self, data: List[dict]) -> str:
        # Tab-separated values for easy parsing
        if not data:
            return ""

        keys = data[0].keys()
        lines = ['\t'.join(keys)]

        for row in data:
            lines.append('\t'.join(str(row[k]) for k in keys))

        return '\n'.join(lines)
```

### Format Selection
```python
def get_formatter(format_type: str) -> OutputFormatter:
    formatters = {
        'table': TableFormatter(),
        'json': JSONFormatter(),
        'tsv': MachineFormatter(),
    }
    return formatters.get(format_type, TableFormatter())
```

## Error Handling

### Structured Error Messages
```python
class CLIError(click.ClickException):
    """Base class for CLI errors."""

    def format_message(self):
        return f"Error: {self.message}"

class ValidationError(CLIError):
    """Input validation errors."""

    def format_message(self):
        return f"Validation Error: {self.message}\nUse --help for usage."

class ServiceError(CLIError):
    """Service operation errors."""

    def format_message(self):
        return f"Operation Failed: {self.message}"

class ConfigurationError(CLIError):
    """Configuration errors."""

    def format_message(self):
        return f"Configuration Error: {self.message}\nCheck your settings."
```

### Error Recovery
```python
@cli.command()
def process_with_recovery(
    ctx: click.Context,
    retry: int = 3,
    service: Annotated[Service, Depends(get_service)]
):
    """Process with automatic retry on failure."""

    for attempt in range(retry):
        try:
            result = service.process()
            click.echo(f"Success: {result}")
            return

        except TemporaryError as e:
            if attempt < retry - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                click.echo(f"Attempt {attempt + 1} failed, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise CLIError(f"Failed after {retry} attempts: {e}")

        except PermanentError as e:
            raise CLIError(f"Unrecoverable error: {e}")
```

## Advanced Features

### Interactive Mode
```python
@cli.command()
def interactive():
    """Start interactive mode."""

    # Create REPL
    from prompt_toolkit import prompt
    from prompt_toolkit.completion import WordCompleter

    commands = ['feeds', 'db', 'apify', 'analyze', 'help', 'exit']
    completer = WordCompleter(commands)

    click.echo("Local Newsifier Interactive Mode")
    click.echo("Type 'help' for commands, 'exit' to quit")

    while True:
        try:
            # Get input with autocomplete
            user_input = prompt('nf> ', completer=completer)

            if user_input == 'exit':
                break

            # Parse and execute command
            args = shlex.split(user_input)
            ctx.invoke(cli, args)

        except Exception as e:
            click.echo(f"Error: {e}")
```

### Progress Tracking
```python
@cli.command()
def process_batch(
    files: List[str],
    service: Annotated[Service, Depends(get_service)]
):
    """Process multiple files with progress bar."""

    with click.progressbar(
        files,
        label='Processing files',
        show_pos=True,
        show_percent=True
    ) as bar:
        for file in bar:
            try:
                service.process_file(file)
            except Exception as e:
                click.echo(f"\nError processing {file}: {e}", err=True)
```

### Configuration Management
```python
# Config file support
@cli.command()
@click.option('--config', type=click.Path(exists=True),
              help='Path to config file')
def process_with_config(config: str):
    """Process using configuration file."""

    # Load config
    if config:
        with open(config) as f:
            settings = yaml.safe_load(f)
    else:
        settings = load_default_config()

    # Validate config
    validated = ConfigSchema(**settings)

    # Use config
    service = create_service(validated)
    service.process()
```

### Multi-Environment Support
```python
@cli.command()
@click.option('--env', type=click.Choice(['dev', 'staging', 'prod']),
              default='dev')
def deploy(env: str):
    """Deploy to specified environment."""

    # Load environment-specific config
    env_config = load_env_config(env)

    # Confirm for production
    if env == 'prod':
        if not click.confirm('Deploy to production?'):
            click.echo('Deployment cancelled.')
            return

    # Deploy
    deployer = Deployer(env_config)
    deployer.deploy()
```

## Database Operations

### Inspection Commands
```python
@db_cli.command()
@click.argument('table', type=click.Choice(['articles', 'entities', 'feeds']))
@click.argument('id', type=int)
def inspect(
    table: str,
    id: int,
    session: Annotated[Session, Depends(get_session)]
):
    """Inspect a specific database record."""

    # Map table names to models
    models = {
        'articles': Article,
        'entities': Entity,
        'feeds': RSSFeed
    }

    model = models[table]
    record = session.get(model, id)

    if not record:
        raise click.ClickException(f"No {table} found with ID {id}")

    # Display record details
    console = Console()

    # Create pretty table
    table_display = Table(title=f"{table.title()} ID: {id}")
    table_display.add_column("Field", style="cyan")
    table_display.add_column("Value", style="green")

    # Add fields
    for field, value in record.model_dump().items():
        if isinstance(value, datetime):
            value = value.isoformat()
        elif isinstance(value, list):
            value = f"[{len(value)} items]"

        table_display.add_row(field, str(value))

    console.print(table_display)
```

### Integrity Verification
```python
@db_cli.command()
def verify(
    session: Annotated[Session, Depends(get_session)]
):
    """Verify database integrity."""

    issues = []

    # Check for orphaned entities
    orphaned_entities = session.query(Entity).filter(
        ~Entity.article_id.in_(
            session.query(Article.id)
        )
    ).count()

    if orphaned_entities:
        issues.append(f"Found {orphaned_entities} orphaned entities")

    # Check for duplicate URLs
    duplicates = session.query(
        Article.url,
        func.count(Article.id).label('count')
    ).group_by(Article.url).having(
        func.count(Article.id) > 1
    ).all()

    if duplicates:
        issues.append(f"Found {len(duplicates)} duplicate URLs")

    # Check for invalid data
    invalid_articles = session.query(Article).filter(
        or_(
            Article.title == '',
            Article.content == '',
            Article.url == ''
        )
    ).count()

    if invalid_articles:
        issues.append(f"Found {invalid_articles} articles with empty fields")

    # Display results
    if issues:
        click.echo("Database integrity issues found:")
        for issue in issues:
            click.echo(f"  - {issue}")
        raise click.ClickException("Database verification failed")
    else:
        click.echo("✓ Database integrity verified")
```

## Testing Strategies

### CLI Test Fixtures
```python
@pytest.fixture
def cli_runner():
    """Create a CLI runner for testing."""
    return CliRunner()

@pytest.fixture
def isolated_cli_runner(tmp_path):
    """Create an isolated CLI runner with temp directory."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        yield runner

@pytest.fixture
def mock_services():
    """Mock all service dependencies."""
    with patch.multiple(
        'local_newsifier.di.providers',
        get_feed_service=Mock(),
        get_article_service=Mock(),
        get_apify_service=Mock()
    ) as mocks:
        yield mocks
```

### Testing Patterns
```python
def test_command_success(cli_runner, mock_services):
    """Test successful command execution."""
    # Setup
    mock_service = Mock()
    mock_service.operation.return_value = "Success"
    mock_services['get_service'].return_value = mock_service

    # Execute
    result = cli_runner.invoke(cli, ['command'])

    # Verify
    assert result.exit_code == 0
    assert "Success" in result.output
    mock_service.operation.assert_called_once()

def test_command_error_handling(cli_runner, mock_services):
    """Test error handling."""
    # Setup
    mock_service = Mock()
    mock_service.operation.side_effect = ServiceError("Failed")
    mock_services['get_service'].return_value = mock_service

    # Execute
    result = cli_runner.invoke(cli, ['command'])

    # Verify
    assert result.exit_code == 1
    assert "Failed" in result.output

def test_command_with_input(cli_runner):
    """Test command with user input."""
    result = cli_runner.invoke(
        cli,
        ['interactive-command'],
        input='yes\ntest input\n'
    )

    assert result.exit_code == 0
    assert "Confirmed" in result.output
```

## Best Practices

### 1. Command Design
- Keep commands focused and single-purpose
- Use consistent naming conventions
- Provide helpful descriptions and examples
- Support both human and machine-readable output

### 2. Option Design
- Use standard option names (--verbose, --format, --output)
- Provide sensible defaults
- Validate options early
- Use option groups for related options

### 3. Error Messages
- Be specific about what went wrong
- Suggest how to fix the problem
- Include relevant context
- Use consistent error format

### 4. Performance
- Show progress for long operations
- Support dry-run mode
- Implement pagination for large results
- Cache expensive operations

### 5. Documentation
- Include examples in help text
- Document exit codes
- Provide man pages
- Keep README up to date

## Future Enhancements

### 1. Plugin System
```python
# Plugin interface
class CLIPlugin(ABC):
    @abstractmethod
    def get_commands(self) -> List[click.Command]:
        pass

# Plugin loading
def load_plugins():
    plugins = []
    for entry_point in pkg_resources.iter_entry_points('nf.plugins'):
        plugin_class = entry_point.load()
        plugins.append(plugin_class())
    return plugins

# Register plugin commands
for plugin in load_plugins():
    for command in plugin.get_commands():
        cli.add_command(command)
```

### 2. Shell Completion
```bash
# Bash completion
_nf_completion() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # Command completion logic
    opts=$(nf --get-completions "$COMP_LINE")
    COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )

    return 0
}

complete -F _nf_completion nf
```

### 3. Remote Execution
```python
@cli.command()
@click.option('--remote', help='Remote server to execute on')
def remote_command(remote: str):
    """Execute command on remote server."""

    if remote:
        # SSH to remote and execute
        ssh_client = paramiko.SSHClient()
        ssh_client.connect(remote)

        stdin, stdout, stderr = ssh_client.exec_command(
            f'nf {" ".join(sys.argv[2:])}'
        )

        click.echo(stdout.read().decode())
```

## References

- [Click Documentation](https://click.palletsprojects.com/)
- [Rich CLI Formatting](https://rich.readthedocs.io/)
- Project Issues: #136, #172, #208, #251, #294, #337, #380, #423, #466, #509, #552, #595, #638
