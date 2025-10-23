"""Centralized CLI utilities and common patterns."""

import asyncio
import json
import os
from typing import Optional, Dict, Any, Callable, TypeVar, List
from pathlib import Path
from functools import wraps

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core import Task, TicketState, Priority, AdapterRegistry
from ..core.config import get_config, get_adapter_config
from ..queue import Queue, WorkerManager, QueueStatus

# Type variable for async functions
T = TypeVar('T')

console = Console()


class CommonPatterns:
    """Common CLI patterns and utilities."""

    # Configuration file management
    CONFIG_FILE = Path.home() / ".mcp-ticketer" / "config.json"

    @staticmethod
    def load_config() -> dict:
        """Load configuration from file."""
        if CommonPatterns.CONFIG_FILE.exists():
            with open(CommonPatterns.CONFIG_FILE, "r") as f:
                return json.load(f)
        return {"adapter": "aitrackdown", "config": {"base_path": ".aitrackdown"}}

    @staticmethod
    def save_config(config: dict) -> None:
        """Save configuration to file."""
        CommonPatterns.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CommonPatterns.CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)

    @staticmethod
    def merge_config(updates: dict) -> dict:
        """Merge updates into existing config."""
        config = CommonPatterns.load_config()

        # Handle default_adapter
        if "default_adapter" in updates:
            config["default_adapter"] = updates["default_adapter"]

        # Handle adapter-specific configurations
        if "adapters" in updates:
            if "adapters" not in config:
                config["adapters"] = {}
            for adapter_name, adapter_config in updates["adapters"].items():
                if adapter_name not in config["adapters"]:
                    config["adapters"][adapter_name] = {}
                config["adapters"][adapter_name].update(adapter_config)

        return config

    @staticmethod
    def get_adapter(override_adapter: Optional[str] = None, override_config: Optional[dict] = None):
        """Get configured adapter instance with environment variable support."""
        config = CommonPatterns.load_config()

        # Use override adapter if provided, otherwise use default
        if override_adapter:
            adapter_type = override_adapter
            # If we have a stored config for this adapter, use it
            adapters_config = config.get("adapters", {})
            adapter_config = adapters_config.get(adapter_type, {})
            # Override with provided config if any
            if override_config:
                adapter_config.update(override_config)
        else:
            # Use default adapter from config
            adapter_type = config.get("default_adapter", "aitrackdown")
            # Get config for the default adapter
            adapters_config = config.get("adapters", {})
            adapter_config = adapters_config.get(adapter_type, {})

        # Fallback to legacy config format for backward compatibility
        if not adapter_config and "config" in config:
            adapter_config = config["config"]

        # Add environment variables for authentication
        adapter_config = CommonPatterns._add_env_auth(adapter_type, adapter_config)

        return AdapterRegistry.get_adapter(adapter_type, adapter_config)

    @staticmethod
    def _add_env_auth(adapter_type: str, adapter_config: dict) -> dict:
        """Add environment variable authentication to adapter config."""
        auth_mapping = {
            "linear": [("api_key", "LINEAR_API_KEY")],
            "github": [("api_key", "GITHUB_TOKEN"), ("token", "GITHUB_TOKEN")],
            "jira": [("api_token", "JIRA_ACCESS_TOKEN"), ("email", "JIRA_ACCESS_USER")],
        }

        if adapter_type in auth_mapping:
            for config_key, env_var in auth_mapping[adapter_type]:
                if not adapter_config.get(config_key):
                    env_value = os.getenv(env_var)
                    if env_value:
                        adapter_config[config_key] = env_value

        return adapter_config

    @staticmethod
    def queue_operation(
        ticket_data: Dict[str, Any],
        operation: str,
        adapter_name: Optional[str] = None,
        show_progress: bool = True
    ) -> str:
        """Queue an operation and optionally start the worker."""
        if not adapter_name:
            config = CommonPatterns.load_config()
            adapter_name = config.get("default_adapter", "aitrackdown")

        # Add to queue
        queue = Queue()
        queue_id = queue.add(
            ticket_data=ticket_data,
            adapter=adapter_name,
            operation=operation
        )

        if show_progress:
            console.print(f"[green]✓[/green] Queued {operation}: {queue_id}")
            console.print("[dim]Use 'mcp-ticketer check {queue_id}' to check progress[/dim]")

        # Start worker if needed
        manager = WorkerManager()
        if manager.start_if_needed():
            if show_progress:
                console.print("[dim]Worker started to process request[/dim]")

        return queue_id

    @staticmethod
    def display_ticket_table(tickets: List[Task], title: str = "Tickets") -> None:
        """Display tickets in a formatted table."""
        if not tickets:
            console.print("[yellow]No tickets found[/yellow]")
            return

        table = Table(title=title)
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Title", style="white")
        table.add_column("State", style="green")
        table.add_column("Priority", style="yellow")
        table.add_column("Assignee", style="blue")

        for ticket in tickets:
            table.add_row(
                ticket.id or "N/A",
                ticket.title,
                ticket.state,
                ticket.priority,
                ticket.assignee or "-",
            )

        console.print(table)

    @staticmethod
    def display_ticket_details(ticket: Task, comments: Optional[List] = None) -> None:
        """Display detailed ticket information."""
        console.print(f"\n[bold]Ticket: {ticket.id}[/bold]")
        console.print(f"Title: {ticket.title}")
        console.print(f"State: [green]{ticket.state}[/green]")
        console.print(f"Priority: [yellow]{ticket.priority}[/yellow]")

        if ticket.description:
            console.print(f"\n[dim]Description:[/dim]")
            console.print(ticket.description)

        if ticket.tags:
            console.print(f"\nTags: {', '.join(ticket.tags)}")

        if ticket.assignee:
            console.print(f"Assignee: {ticket.assignee}")

        # Display comments if provided
        if comments:
            console.print(f"\n[bold]Comments ({len(comments)}):[/bold]")
            for comment in comments:
                console.print(f"\n[dim]{comment.created_at} - {comment.author}:[/dim]")
                console.print(comment.content)

    @staticmethod
    def display_queue_status() -> None:
        """Display queue and worker status."""
        queue = Queue()
        manager = WorkerManager()

        # Get queue stats
        stats = queue.get_stats()
        pending = stats.get(QueueStatus.PENDING.value, 0)

        # Show queue status
        console.print("[bold]Queue Status:[/bold]")
        console.print(f"  Pending: {pending}")
        console.print(f"  Processing: {stats.get(QueueStatus.PROCESSING.value, 0)}")
        console.print(f"  Completed: {stats.get(QueueStatus.COMPLETED.value, 0)}")
        console.print(f"  Failed: {stats.get(QueueStatus.FAILED.value, 0)}")

        # Show worker status
        worker_status = manager.get_status()
        if worker_status["running"]:
            console.print(f"\n[green]● Worker is running[/green] (PID: {worker_status.get('pid')})")
        else:
            console.print("\n[red]○ Worker is not running[/red]")
            if pending > 0:
                console.print("[yellow]Note: There are pending items. Start worker with 'mcp-ticketer queue start'[/yellow]")


def async_command(f: Callable[..., T]) -> Callable[..., T]:
    """Decorator to handle async CLI commands."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper


def with_adapter(f: Callable) -> Callable:
    """Decorator to inject adapter instance into CLI commands."""
    @wraps(f)
    def wrapper(adapter: Optional[str] = None, *args, **kwargs):
        adapter_instance = CommonPatterns.get_adapter(override_adapter=adapter)
        return f(adapter_instance, *args, **kwargs)
    return wrapper


def with_progress(message: str = "Processing..."):
    """Decorator to show progress spinner for long-running operations."""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                progress.add_task(description=message, total=None)
                return f(*args, **kwargs)
        return wrapper
    return decorator


def validate_required_fields(**field_map):
    """Decorator to validate required fields are provided."""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            missing_fields = []
            for field_name, display_name in field_map.items():
                if field_name in kwargs and kwargs[field_name] is None:
                    missing_fields.append(display_name)

            if missing_fields:
                console.print(f"[red]Error:[/red] Missing required fields: {', '.join(missing_fields)}")
                raise typer.Exit(1)

            return f(*args, **kwargs)
        return wrapper
    return decorator


def handle_adapter_errors(f: Callable) -> Callable:
    """Decorator to handle common adapter errors gracefully."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ConnectionError as e:
            console.print(f"[red]Connection Error:[/red] {e}")
            console.print("Check your network connection and adapter configuration")
            raise typer.Exit(1)
        except ValueError as e:
            console.print(f"[red]Configuration Error:[/red] {e}")
            console.print("Run 'mcp-ticketer init' to configure your adapter")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[red]Unexpected Error:[/red] {e}")
            raise typer.Exit(1)
    return wrapper


class ConfigValidator:
    """Configuration validation utilities."""

    @staticmethod
    def validate_adapter_config(adapter_type: str, config: dict) -> List[str]:
        """Validate adapter configuration and return list of issues."""
        issues = []

        validation_rules = {
            "github": [
                ("token", "GitHub token"),
                ("owner", "Repository owner"),
                ("repo", "Repository name"),
            ],
            "jira": [
                ("server", "JIRA server URL"),
                ("email", "User email"),
                ("api_token", "API token"),
            ],
            "linear": [
                ("api_key", "API key"),
                ("team_key", "Team key"),
            ],
            "aitrackdown": [
                ("base_path", "Base path"),
            ],
        }

        if adapter_type in validation_rules:
            for field, display_name in validation_rules[adapter_type]:
                if not config.get(field):
                    env_var = ConfigValidator._get_env_var(adapter_type, field)
                    if env_var and not os.getenv(env_var):
                        issues.append(f"Missing {display_name} (config.{field} or {env_var})")

        return issues

    @staticmethod
    def _get_env_var(adapter_type: str, field: str) -> Optional[str]:
        """Get corresponding environment variable name for a config field."""
        env_mapping = {
            "github": {"token": "GITHUB_TOKEN", "owner": "GITHUB_OWNER", "repo": "GITHUB_REPO"},
            "jira": {"api_token": "JIRA_API_TOKEN", "email": "JIRA_EMAIL", "server": "JIRA_SERVER"},
            "linear": {"api_key": "LINEAR_API_KEY"},
        }
        return env_mapping.get(adapter_type, {}).get(field)


class CommandBuilder:
    """Builder for common CLI command patterns."""

    def __init__(self):
        self._validators = []
        self._handlers = []
        self._decorators = []

    def with_adapter_validation(self):
        """Add adapter configuration validation."""
        self._validators.append(self._validate_adapter)
        return self

    def with_async_support(self):
        """Add async support to command."""
        self._decorators.append(async_command)
        return self

    def with_error_handling(self):
        """Add error handling decorator."""
        self._decorators.append(handle_adapter_errors)
        return self

    def with_progress(self, message: str = "Processing..."):
        """Add progress spinner."""
        self._decorators.append(with_progress(message))
        return self

    def build(self, func: Callable) -> Callable:
        """Build the decorated function."""
        decorated_func = func
        for decorator in reversed(self._decorators):
            decorated_func = decorator(decorated_func)
        return decorated_func

    def _validate_adapter(self, *args, **kwargs):
        """Validate adapter configuration."""
        config = CommonPatterns.load_config()
        default_adapter = config.get("default_adapter", "aitrackdown")
        adapter_config = config.get("adapters", {}).get(default_adapter, {})

        issues = ConfigValidator.validate_adapter_config(default_adapter, adapter_config)
        if issues:
            console.print("[red]Configuration Issues:[/red]")
            for issue in issues:
                console.print(f"  • {issue}")
            console.print("Run 'mcp-ticketer init' to fix configuration")
            raise typer.Exit(1)


def create_standard_ticket_command(operation: str):
    """Create a standard ticket operation command."""
    def command_template(
        ticket_id: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[Priority] = None,
        state: Optional[TicketState] = None,
        assignee: Optional[str] = None,
        tags: Optional[List[str]] = None,
        adapter: Optional[str] = None,
    ):
        """Template for ticket commands."""
        # Build ticket data
        ticket_data = {}
        if ticket_id:
            ticket_data["ticket_id"] = ticket_id
        if title:
            ticket_data["title"] = title
        if description:
            ticket_data["description"] = description
        if priority:
            ticket_data["priority"] = priority.value if hasattr(priority, 'value') else priority
        if state:
            ticket_data["state"] = state.value if hasattr(state, 'value') else state
        if assignee:
            ticket_data["assignee"] = assignee
        if tags:
            ticket_data["tags"] = tags

        # Queue the operation
        queue_id = CommonPatterns.queue_operation(ticket_data, operation, adapter)

        # Show confirmation
        console.print(f"[green]✓[/green] Queued {operation}: {queue_id}")
        return queue_id

    return command_template


# Reusable command components
class TicketCommands:
    """Reusable ticket command implementations."""

    @staticmethod
    @async_command
    @handle_adapter_errors
    async def list_tickets(
        adapter_instance,
        state: Optional[TicketState] = None,
        priority: Optional[Priority] = None,
        limit: int = 10
    ):
        """List tickets with filters."""
        filters = {}
        if state:
            filters["state"] = state
        if priority:
            filters["priority"] = priority

        tickets = await adapter_instance.list(limit=limit, filters=filters)
        CommonPatterns.display_ticket_table(tickets)

    @staticmethod
    @async_command
    @handle_adapter_errors
    async def show_ticket(
        adapter_instance,
        ticket_id: str,
        show_comments: bool = False
    ):
        """Show ticket details."""
        ticket = await adapter_instance.read(ticket_id)
        if not ticket:
            console.print(f"[red]✗[/red] Ticket not found: {ticket_id}")
            raise typer.Exit(1)

        comments = None
        if show_comments:
            comments = await adapter_instance.get_comments(ticket_id)

        CommonPatterns.display_ticket_details(ticket, comments)

    @staticmethod
    def create_ticket(
        title: str,
        description: Optional[str] = None,
        priority: Priority = Priority.MEDIUM,
        tags: Optional[List[str]] = None,
        assignee: Optional[str] = None,
        adapter: Optional[str] = None
    ) -> str:
        """Create a new ticket."""
        ticket_data = {
            "title": title,
            "description": description,
            "priority": priority.value if isinstance(priority, Priority) else priority,
            "tags": tags or [],
            "assignee": assignee,
        }

        return CommonPatterns.queue_operation(ticket_data, "create", adapter)

    @staticmethod
    def update_ticket(
        ticket_id: str,
        updates: Dict[str, Any],
        adapter: Optional[str] = None
    ) -> str:
        """Update a ticket."""
        if not updates:
            console.print("[yellow]No updates specified[/yellow]")
            raise typer.Exit(1)

        updates["ticket_id"] = ticket_id
        return CommonPatterns.queue_operation(updates, "update", adapter)

    @staticmethod
    def transition_ticket(
        ticket_id: str,
        state: TicketState,
        adapter: Optional[str] = None
    ) -> str:
        """Transition ticket state."""
        ticket_data = {
            "ticket_id": ticket_id,
            "state": state.value if hasattr(state, 'value') else state
        }

        return CommonPatterns.queue_operation(ticket_data, "transition", adapter)