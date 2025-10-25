"""CLI implementation using Typer."""

import asyncio
import json
import os
from enum import Enum
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from ..__version__ import __version__
from ..core import AdapterRegistry, Priority, TicketState
from ..core.models import SearchQuery, Comment
from ..queue import Queue, QueueStatus, WorkerManager
from ..queue.health_monitor import QueueHealthMonitor, HealthStatus
from ..queue.ticket_registry import TicketRegistry

# Import adapters module to trigger registration
import mcp_ticketer.adapters  # noqa: F401
from .configure import configure_wizard, set_adapter_config, show_current_config
from .diagnostics import run_diagnostics
from .discover import app as discover_app
from .linear_commands import app as linear_app
from .migrate_config import migrate_config_command
from .queue_commands import app as queue_app

# Load environment variables from .env files
# Priority: .env.local (highest) > .env (base)
# This matches the pattern used in worker.py and server.py

# Load .env first (base configuration)
load_dotenv()

# Load .env.local with override=True (project-specific overrides)
env_local = Path.cwd() / ".env.local"
if env_local.exists():
    load_dotenv(env_local, override=True)

app = typer.Typer(
    name="mcp-ticketer",
    help="Universal ticket management interface",
    add_completion=False,
)
console = Console()


def version_callback(value: bool):
    """Print version and exit."""
    if value:
        console.print(f"mcp-ticketer version {__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
):
    """MCP Ticketer - Universal ticket management interface."""
    pass


# Configuration file management - PROJECT-LOCAL ONLY
CONFIG_FILE = Path.cwd() / ".mcp-ticketer" / "config.json"


class AdapterType(str, Enum):
    """Available adapter types."""

    AITRACKDOWN = "aitrackdown"
    LINEAR = "linear"
    JIRA = "jira"
    GITHUB = "github"


def load_config(project_dir: Optional[Path] = None) -> dict:
    """Load configuration from project-local config file ONLY.

    SECURITY: This method ONLY reads from the current project directory
    to prevent configuration leakage across projects. It will NEVER read
    from user home directory or system-wide locations.

    Args:
        project_dir: Optional project directory to load config from

    Resolution order:
    1. Project-specific config (.mcp-ticketer/config.json in project_dir or cwd)
    2. Default to aitrackdown adapter

    Returns:
        Configuration dictionary with adapter and config keys.
        Defaults to aitrackdown if no local config exists.

    """
    import logging

    logger = logging.getLogger(__name__)

    # Use provided project_dir or current working directory
    base_dir = project_dir or Path.cwd()

    # ONLY check project-specific config in project directory
    project_config = base_dir / ".mcp-ticketer" / "config.json"
    if project_config.exists():
        # Validate that config file is actually in project directory
        try:
            if not project_config.resolve().is_relative_to(base_dir.resolve()):
                logger.error(
                    f"Security violation: Config file {project_config} "
                    "is not within project directory"
                )
                raise ValueError(
                    f"Security violation: Config file {project_config} "
                    "is not within project directory"
                )
        except (ValueError, RuntimeError):
            # is_relative_to may raise ValueError in some cases
            pass

        try:
            with open(project_config) as f:
                config = json.load(f)
                logger.info(
                    f"Loaded configuration from project-local: {project_config}"
                )
                return config
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load project config: {e}, using defaults")
            console.print(
                f"[yellow]Warning: Could not load project config: {e}[/yellow]"
            )

    # Default to aitrackdown with local base path
    logger.info("No project-local config found, defaulting to aitrackdown adapter")
    return {"adapter": "aitrackdown", "config": {"base_path": ".aitrackdown"}}


def _discover_from_env_files() -> Optional[str]:
    """Discover adapter configuration from .env or .env.local files.

    Returns:
        Adapter name if discovered, None otherwise
    """
    import os
    import logging
    from pathlib import Path

    logger = logging.getLogger(__name__)

    # Check .env.local first, then .env
    env_files = [".env.local", ".env"]

    for env_file in env_files:
        env_path = Path.cwd() / env_file
        if env_path.exists():
            try:
                # Simple .env parsing (key=value format)
                env_vars = {}
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            env_vars[key.strip()] = value.strip().strip('"\'')

                # Check for adapter-specific variables
                if env_vars.get("LINEAR_API_KEY"):
                    logger.info(f"Discovered Linear configuration in {env_file}")
                    return "linear"
                elif env_vars.get("GITHUB_TOKEN"):
                    logger.info(f"Discovered GitHub configuration in {env_file}")
                    return "github"
                elif env_vars.get("JIRA_SERVER"):
                    logger.info(f"Discovered JIRA configuration in {env_file}")
                    return "jira"

            except Exception as e:
                logger.warning(f"Could not read {env_file}: {e}")

    return None


def _save_adapter_to_config(adapter_name: str) -> None:
    """Save adapter configuration to config file.

    Args:
        adapter_name: Name of the adapter to save as default
    """
    import logging

    logger = logging.getLogger(__name__)

    try:
        config = load_config()
        config["default_adapter"] = adapter_name

        # Ensure adapters section exists
        if "adapters" not in config:
            config["adapters"] = {}

        # Add basic adapter config if not exists
        if adapter_name not in config["adapters"]:
            if adapter_name == "aitrackdown":
                config["adapters"][adapter_name] = {"base_path": ".aitrackdown"}
            else:
                config["adapters"][adapter_name] = {"type": adapter_name}

        save_config(config)
        logger.info(f"Saved {adapter_name} as default adapter")

    except Exception as e:
        logger.warning(f"Could not save adapter configuration: {e}")


def save_config(config: dict) -> None:
    """Save configuration to project-local config file ONLY.

    SECURITY: This method ONLY saves to the current project directory
    to prevent configuration leakage across projects.
    """
    import logging

    logger = logging.getLogger(__name__)

    project_config = Path.cwd() / ".mcp-ticketer" / "config.json"
    project_config.parent.mkdir(parents=True, exist_ok=True)
    with open(project_config, "w") as f:
        json.dump(config, f, indent=2)
    logger.info(f"Saved configuration to project-local: {project_config}")


def merge_config(updates: dict) -> dict:
    """Merge updates into existing config.

    Args:
        updates: Configuration updates to merge

    Returns:
        Updated configuration

    """
    config = load_config()

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


def get_adapter(
    override_adapter: Optional[str] = None, override_config: Optional[dict] = None
):
    """Get configured adapter instance.

    Args:
        override_adapter: Override the default adapter type
        override_config: Override configuration for the adapter

    """
    config = load_config()

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
    import os

    if adapter_type == "linear":
        if not adapter_config.get("api_key"):
            adapter_config["api_key"] = os.getenv("LINEAR_API_KEY")
    elif adapter_type == "github":
        if not adapter_config.get("api_key") and not adapter_config.get("token"):
            adapter_config["api_key"] = os.getenv("GITHUB_TOKEN")
    elif adapter_type == "jira":
        if not adapter_config.get("api_token"):
            adapter_config["api_token"] = os.getenv("JIRA_ACCESS_TOKEN")
        if not adapter_config.get("email"):
            adapter_config["email"] = os.getenv("JIRA_ACCESS_USER")

    return AdapterRegistry.get_adapter(adapter_type, adapter_config)


def _prompt_for_adapter_selection(console: Console) -> str:
    """Interactive prompt for adapter selection.

    Args:
        console: Rich console for output

    Returns:
        Selected adapter type
    """
    console.print("\n[bold blue]🚀 MCP Ticketer Setup[/bold blue]")
    console.print("Choose which ticket system you want to connect to:\n")

    # Define adapter options with descriptions
    adapters = [
        {
            "name": "linear",
            "title": "Linear",
            "description": "Modern project management (linear.app)",
            "requirements": "API key and team ID"
        },
        {
            "name": "github",
            "title": "GitHub Issues",
            "description": "GitHub repository issues",
            "requirements": "Personal access token, owner, and repo"
        },
        {
            "name": "jira",
            "title": "JIRA",
            "description": "Atlassian JIRA project management",
            "requirements": "Server URL, email, and API token"
        },
        {
            "name": "aitrackdown",
            "title": "Local Files (AITrackdown)",
            "description": "Store tickets in local files (no external service)",
            "requirements": "None - works offline"
        }
    ]

    # Display options
    for i, adapter in enumerate(adapters, 1):
        console.print(f"[cyan]{i}.[/cyan] [bold]{adapter['title']}[/bold]")
        console.print(f"   {adapter['description']}")
        console.print(f"   [dim]Requirements: {adapter['requirements']}[/dim]\n")

    # Get user selection
    while True:
        try:
            choice = typer.prompt(
                "Select adapter (1-4)",
                type=int,
                default=1
            )
            if 1 <= choice <= len(adapters):
                selected_adapter = adapters[choice - 1]
                console.print(f"\n[green]✓ Selected: {selected_adapter['title']}[/green]")
                return selected_adapter["name"]
            else:
                console.print(f"[red]Please enter a number between 1 and {len(adapters)}[/red]")
        except (ValueError, typer.Abort):
            console.print("[yellow]Setup cancelled.[/yellow]")
            raise typer.Exit(0)


@app.command()
def setup(
    adapter: Optional[str] = typer.Option(
        None,
        "--adapter",
        "-a",
        help="Adapter type to use (interactive prompt if not specified)",
    ),
    project_path: Optional[str] = typer.Option(
        None, "--path", help="Project path (default: current directory)"
    ),
    global_config: bool = typer.Option(
        False,
        "--global",
        "-g",
        help="Save to global config instead of project-specific",
    ),
    base_path: Optional[str] = typer.Option(
        None,
        "--base-path",
        "-p",
        help="Base path for ticket storage (AITrackdown only)",
    ),
    api_key: Optional[str] = typer.Option(
        None, "--api-key", help="API key for Linear or API token for JIRA"
    ),
    team_id: Optional[str] = typer.Option(
        None, "--team-id", help="Linear team ID (required for Linear adapter)"
    ),
    jira_server: Optional[str] = typer.Option(
        None,
        "--jira-server",
        help="JIRA server URL (e.g., https://company.atlassian.net)",
    ),
    jira_email: Optional[str] = typer.Option(
        None, "--jira-email", help="JIRA user email for authentication"
    ),
    jira_project: Optional[str] = typer.Option(
        None, "--jira-project", help="Default JIRA project key"
    ),
    github_owner: Optional[str] = typer.Option(
        None, "--github-owner", help="GitHub repository owner"
    ),
    github_repo: Optional[str] = typer.Option(
        None, "--github-repo", help="GitHub repository name"
    ),
    github_token: Optional[str] = typer.Option(
        None, "--github-token", help="GitHub Personal Access Token"
    ),
) -> None:
    """Interactive setup wizard for MCP Ticketer (alias for init).

    This command provides a user-friendly setup experience with prompts
    to guide you through configuring MCP Ticketer for your preferred
    ticket management system. It's identical to 'init' and 'install'.

    Examples:
        # Run interactive setup
        mcp-ticketer setup

        # Setup with specific adapter
        mcp-ticketer setup --adapter linear

        # Setup for different project
        mcp-ticketer setup --path /path/to/project
    """
    # Call init with all parameters
    init(
        adapter=adapter,
        project_path=project_path,
        global_config=global_config,
        base_path=base_path,
        api_key=api_key,
        team_id=team_id,
        jira_server=jira_server,
        jira_email=jira_email,
        jira_project=jira_project,
        github_owner=github_owner,
        github_repo=github_repo,
        github_token=github_token,
    )


@app.command()
def init(
    adapter: Optional[str] = typer.Option(
        None,
        "--adapter",
        "-a",
        help="Adapter type to use (interactive prompt if not specified)",
    ),
    project_path: Optional[str] = typer.Option(
        None, "--path", help="Project path (default: current directory)"
    ),
    global_config: bool = typer.Option(
        False,
        "--global",
        "-g",
        help="Save to global config instead of project-specific",
    ),
    base_path: Optional[str] = typer.Option(
        None,
        "--base-path",
        "-p",
        help="Base path for ticket storage (AITrackdown only)",
    ),
    api_key: Optional[str] = typer.Option(
        None, "--api-key", help="API key for Linear or API token for JIRA"
    ),
    team_id: Optional[str] = typer.Option(
        None, "--team-id", help="Linear team ID (required for Linear adapter)"
    ),
    jira_server: Optional[str] = typer.Option(
        None,
        "--jira-server",
        help="JIRA server URL (e.g., https://company.atlassian.net)",
    ),
    jira_email: Optional[str] = typer.Option(
        None, "--jira-email", help="JIRA user email for authentication"
    ),
    jira_project: Optional[str] = typer.Option(
        None, "--jira-project", help="Default JIRA project key"
    ),
    github_owner: Optional[str] = typer.Option(
        None, "--github-owner", help="GitHub repository owner"
    ),
    github_repo: Optional[str] = typer.Option(
        None, "--github-repo", help="GitHub repository name"
    ),
    github_token: Optional[str] = typer.Option(
        None, "--github-token", help="GitHub Personal Access Token"
    ),
) -> None:
    """Initialize mcp-ticketer for the current project.

    This command sets up MCP Ticketer configuration with interactive prompts
    to guide you through the process. It auto-detects adapter configuration
    from .env files or prompts for interactive setup if no configuration is found.

    Creates .mcp-ticketer/config.json in the current directory with
    auto-detected or specified adapter configuration.

    Note: 'setup' and 'install' are synonyms for this command.

    Examples:
        # Interactive setup (same as 'setup' and 'install')
        mcp-ticketer init

        # Force specific adapter
        mcp-ticketer init --adapter linear

        # Initialize for different project
        mcp-ticketer init --path /path/to/project

        # Save globally (not recommended)
        mcp-ticketer init --global

    """
    from pathlib import Path

    from ..core.env_discovery import discover_config
    from ..core.project_config import ConfigResolver

    # Determine project path
    proj_path = Path(project_path) if project_path else Path.cwd()

    # Check if already initialized (unless using --global)
    if not global_config:
        config_path = proj_path / ".mcp-ticketer" / "config.json"

        if config_path.exists():
            if not typer.confirm(
                f"Configuration already exists at {config_path}. Overwrite?",
                default=False,
            ):
                console.print("[yellow]Initialization cancelled.[/yellow]")
                raise typer.Exit(0)

    # 1. Try auto-discovery if no adapter specified
    discovered = None
    adapter_type = adapter

    if not adapter_type:
        console.print(
            "[cyan]🔍 Auto-discovering configuration from .env files...[/cyan]"
        )

        # First try our improved .env configuration loader
        from ..mcp.server import _load_env_configuration
        env_config = _load_env_configuration()

        if env_config:
            adapter_type = env_config["adapter_type"]
            console.print(
                f"[green]✓ Detected {adapter_type} adapter from environment files[/green]"
            )

            # Show what was discovered
            console.print(f"\n[dim]Configuration found in: .env files[/dim]")
            console.print(f"[dim]Confidence: 100%[/dim]")

            # Ask user to confirm auto-detected adapter
            if not typer.confirm(
                f"Use detected {adapter_type} adapter?",
                default=True,
            ):
                adapter_type = None  # Will trigger interactive selection
        else:
            # Fallback to old discovery system for backward compatibility
            discovered = discover_config(proj_path)

            if discovered and discovered.adapters:
                primary = discovered.get_primary_adapter()
                if primary:
                    adapter_type = primary.adapter_type
                    console.print(
                        f"[green]✓ Detected {adapter_type} adapter from environment files[/green]"
                    )

                    # Show what was discovered
                    console.print(
                        f"\n[dim]Configuration found in: {primary.found_in}[/dim]"
                    )
                    console.print(f"[dim]Confidence: {primary.confidence:.0%}[/dim]")

                    # Ask user to confirm auto-detected adapter
                    if not typer.confirm(
                        f"Use detected {adapter_type} adapter?",
                        default=True,
                    ):
                        adapter_type = None  # Will trigger interactive selection
                else:
                    adapter_type = None  # Will trigger interactive selection
            else:
                adapter_type = None  # Will trigger interactive selection

        # If no adapter determined, show interactive selection
        if not adapter_type:
            adapter_type = _prompt_for_adapter_selection(console)

    # 2. Create configuration based on adapter type
    config = {"default_adapter": adapter_type, "adapters": {}}

    # 3. If discovered and matches adapter_type, use discovered config
    if discovered and adapter_type != "aitrackdown":
        discovered_adapter = discovered.get_adapter_by_type(adapter_type)
        if discovered_adapter:
            adapter_config = discovered_adapter.config.copy()
            # Ensure the config has the correct 'type' field
            adapter_config["type"] = adapter_type
            # Remove 'adapter' field if present (legacy)
            adapter_config.pop("adapter", None)
            config["adapters"][adapter_type] = adapter_config

    # 4. Handle manual configuration for specific adapters
    if adapter_type == "aitrackdown":
        config["adapters"]["aitrackdown"] = {
            "type": "aitrackdown",
            "base_path": base_path or ".aitrackdown"
        }

    elif adapter_type == "linear":
        # If not auto-discovered, build from CLI params or prompt
        if adapter_type not in config["adapters"]:
            linear_config = {}

            # API Key
            linear_api_key = api_key or os.getenv("LINEAR_API_KEY")
            if not linear_api_key and not discovered:
                console.print("\n[bold]Linear Configuration[/bold]")
                console.print("You need a Linear API key to connect to Linear.")
                console.print("[dim]Get your API key at: https://linear.app/settings/api[/dim]\n")

                linear_api_key = typer.prompt(
                    "Enter your Linear API key",
                    hide_input=True
                )

            if linear_api_key:
                linear_config["api_key"] = linear_api_key

            # Team ID
            linear_team_id = team_id or os.getenv("LINEAR_TEAM_ID")
            if not linear_team_id and not discovered:
                console.print("\nYou need your Linear team ID.")
                console.print("[dim]Find it in Linear settings or team URL[/dim]\n")

                linear_team_id = typer.prompt("Enter your Linear team ID")

            if linear_team_id:
                linear_config["team_id"] = linear_team_id

            if not linear_config.get("api_key") or not linear_config.get("team_id"):
                console.print("[red]Error:[/red] Linear requires both API key and team ID")
                console.print("Run 'mcp-ticketer init --adapter linear' with proper credentials")
                raise typer.Exit(1)

            linear_config["type"] = "linear"
            config["adapters"]["linear"] = linear_config

    elif adapter_type == "jira":
        # If not auto-discovered, build from CLI params or prompt
        if adapter_type not in config["adapters"]:
            server = jira_server or os.getenv("JIRA_SERVER")
            email = jira_email or os.getenv("JIRA_EMAIL")
            token = api_key or os.getenv("JIRA_API_TOKEN")
            project = jira_project or os.getenv("JIRA_PROJECT_KEY")

            # Interactive prompts for missing values
            if not server and not discovered:
                console.print("\n[bold]JIRA Configuration[/bold]")
                console.print("Enter your JIRA server details.\n")

                server = typer.prompt(
                    "JIRA server URL (e.g., https://company.atlassian.net)"
                )

            if not email and not discovered:
                email = typer.prompt("Your JIRA email address")

            if not token and not discovered:
                console.print("\nYou need a JIRA API token.")
                console.print("[dim]Generate one at: https://id.atlassian.com/manage/api-tokens[/dim]\n")

                token = typer.prompt(
                    "Enter your JIRA API token",
                    hide_input=True
                )

            if not project and not discovered:
                project = typer.prompt(
                    "Default JIRA project key (optional, press Enter to skip)",
                    default="",
                    show_default=False
                )

            # Validate required fields
            if not server:
                console.print("[red]Error:[/red] JIRA server URL is required")
                raise typer.Exit(1)

            if not email:
                console.print("[red]Error:[/red] JIRA email is required")
                raise typer.Exit(1)

            if not token:
                console.print("[red]Error:[/red] JIRA API token is required")
                raise typer.Exit(1)

            jira_config = {
                "server": server,
                "email": email,
                "api_token": token,
                "type": "jira"
            }

            if project:
                jira_config["project_key"] = project

            config["adapters"]["jira"] = jira_config

    elif adapter_type == "github":
        # If not auto-discovered, build from CLI params or prompt
        if adapter_type not in config["adapters"]:
            owner = github_owner or os.getenv("GITHUB_OWNER")
            repo = github_repo or os.getenv("GITHUB_REPO")
            token = github_token or os.getenv("GITHUB_TOKEN")

            # Interactive prompts for missing values
            if not owner and not discovered:
                console.print("\n[bold]GitHub Configuration[/bold]")
                console.print("Enter your GitHub repository details.\n")

                owner = typer.prompt("GitHub repository owner (username or organization)")

            if not repo and not discovered:
                repo = typer.prompt("GitHub repository name")

            if not token and not discovered:
                console.print("\nYou need a GitHub Personal Access Token.")
                console.print("[dim]Create one at: https://github.com/settings/tokens/new[/dim]")
                console.print("[dim]Required scopes: repo (for private repos) or public_repo (for public repos)[/dim]\n")

                token = typer.prompt(
                    "Enter your GitHub Personal Access Token",
                    hide_input=True
                )

            # Validate required fields
            if not owner:
                console.print("[red]Error:[/red] GitHub repository owner is required")
                raise typer.Exit(1)

            if not repo:
                console.print("[red]Error:[/red] GitHub repository name is required")
                raise typer.Exit(1)

            if not token:
                console.print("[red]Error:[/red] GitHub Personal Access Token is required")
                raise typer.Exit(1)

            config["adapters"]["github"] = {
                "owner": owner,
                "repo": repo,
                "token": token,
                "type": "github"
            }

    # 5. Save to appropriate location
    if global_config:
        # Save to ~/.mcp-ticketer/config.json
        resolver = ConfigResolver(project_path=proj_path)
        config_file_path = resolver.GLOBAL_CONFIG_PATH
        config_file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_file_path, "w") as f:
            json.dump(config, f, indent=2)

        console.print(f"[green]✓ Initialized with {adapter_type} adapter[/green]")
        console.print(f"[dim]Global configuration saved to {config_file_path}[/dim]")
    else:
        # Save to ./.mcp-ticketer/config.json (PROJECT-SPECIFIC)
        config_file_path = proj_path / ".mcp-ticketer" / "config.json"
        config_file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_file_path, "w") as f:
            json.dump(config, f, indent=2)

        console.print(f"[green]✓ Initialized with {adapter_type} adapter[/green]")
        console.print(f"[dim]Project configuration saved to {config_file_path}[/dim]")

        # Add .mcp-ticketer to .gitignore if not already there
        gitignore_path = proj_path / ".gitignore"
        if gitignore_path.exists():
            gitignore_content = gitignore_path.read_text()
            if ".mcp-ticketer" not in gitignore_content:
                with open(gitignore_path, "a") as f:
                    f.write("\n# MCP Ticketer\n.mcp-ticketer/\n")
                console.print("[dim]✓ Added .mcp-ticketer/ to .gitignore[/dim]")
        else:
            # Create .gitignore if it doesn't exist
            with open(gitignore_path, "w") as f:
                f.write("# MCP Ticketer\n.mcp-ticketer/\n")
            console.print("[dim]✓ Created .gitignore with .mcp-ticketer/[/dim]")

    # Show next steps
    _show_next_steps(console, adapter_type, config_file_path)


def _show_next_steps(console: Console, adapter_type: str, config_file_path: Path) -> None:
    """Show helpful next steps after initialization.

    Args:
        console: Rich console for output
        adapter_type: Type of adapter that was configured
        config_file_path: Path to the configuration file
    """
    console.print("\n[bold green]🎉 Setup Complete![/bold green]")
    console.print(f"MCP Ticketer is now configured to use {adapter_type.title()}.\n")

    console.print("[bold]Next Steps:[/bold]")
    console.print("1. [cyan]Test your configuration:[/cyan]")
    console.print("   mcp-ticketer diagnose")
    console.print("\n2. [cyan]Create a test ticket:[/cyan]")
    console.print("   mcp-ticketer create 'Test ticket from MCP Ticketer'")

    if adapter_type != "aitrackdown":
        console.print(f"\n3. [cyan]Verify the ticket appears in {adapter_type.title()}[/cyan]")

        if adapter_type == "linear":
            console.print("   Check your Linear workspace for the new ticket")
        elif adapter_type == "github":
            console.print("   Check your GitHub repository's Issues tab")
        elif adapter_type == "jira":
            console.print("   Check your JIRA project for the new ticket")
    else:
        console.print("\n3. [cyan]Check local ticket storage:[/cyan]")
        console.print("   ls .aitrackdown/")

    console.print("\n4. [cyan]Configure MCP clients (optional):[/cyan]")
    console.print("   mcp-ticketer mcp claude    # For Claude Code")
    console.print("   mcp-ticketer mcp auggie    # For Auggie")
    console.print("   mcp-ticketer mcp gemini    # For Gemini CLI")

    console.print(f"\n[dim]Configuration saved to: {config_file_path}[/dim]")
    console.print("[dim]Run 'mcp-ticketer --help' for more commands[/dim]")


@app.command()
def install(
    adapter: Optional[str] = typer.Option(
        None,
        "--adapter",
        "-a",
        help="Adapter type to use (auto-detected from .env if not specified)",
    ),
    project_path: Optional[str] = typer.Option(
        None, "--path", help="Project path (default: current directory)"
    ),
    global_config: bool = typer.Option(
        False,
        "--global",
        "-g",
        help="Save to global config instead of project-specific",
    ),
    base_path: Optional[str] = typer.Option(
        None,
        "--base-path",
        "-p",
        help="Base path for ticket storage (AITrackdown only)",
    ),
    api_key: Optional[str] = typer.Option(
        None, "--api-key", help="API key for Linear or API token for JIRA"
    ),
    team_id: Optional[str] = typer.Option(
        None, "--team-id", help="Linear team ID (required for Linear adapter)"
    ),
    jira_server: Optional[str] = typer.Option(
        None,
        "--jira-server",
        help="JIRA server URL (e.g., https://company.atlassian.net)",
    ),
    jira_email: Optional[str] = typer.Option(
        None, "--jira-email", help="JIRA user email for authentication"
    ),
    jira_project: Optional[str] = typer.Option(
        None, "--jira-project", help="Default JIRA project key"
    ),
    github_owner: Optional[str] = typer.Option(
        None, "--github-owner", help="GitHub repository owner"
    ),
    github_repo: Optional[str] = typer.Option(
        None, "--github-repo", help="GitHub repository name"
    ),
    github_token: Optional[str] = typer.Option(
        None, "--github-token", help="GitHub Personal Access Token"
    ),
) -> None:
    """Initialize mcp-ticketer for the current project (alias for init).

    This command is synonymous with 'init' and 'setup' - all three provide
    identical functionality with interactive prompts to guide you through
    configuring MCP Ticketer for your preferred ticket management system.

    Examples:
        # Interactive setup (same as 'init' and 'setup')
        mcp-ticketer install

        # Force specific adapter
        mcp-ticketer install --adapter linear

        # Initialize for different project
        mcp-ticketer install --path /path/to/project

        # Save globally (not recommended)
        mcp-ticketer install --global

    """
    # Call init with all parameters
    init(
        adapter=adapter,
        project_path=project_path,
        global_config=global_config,
        base_path=base_path,
        api_key=api_key,
        team_id=team_id,
        jira_server=jira_server,
        jira_email=jira_email,
        jira_project=jira_project,
        github_owner=github_owner,
        github_repo=github_repo,
        github_token=github_token,
    )


@app.command("set")
def set_config(
    adapter: Optional[AdapterType] = typer.Option(
        None, "--adapter", "-a", help="Set default adapter"
    ),
    team_key: Optional[str] = typer.Option(
        None, "--team-key", help="Linear team key (e.g., BTA)"
    ),
    team_id: Optional[str] = typer.Option(None, "--team-id", help="Linear team ID"),
    owner: Optional[str] = typer.Option(
        None, "--owner", help="GitHub repository owner"
    ),
    repo: Optional[str] = typer.Option(None, "--repo", help="GitHub repository name"),
    server: Optional[str] = typer.Option(None, "--server", help="JIRA server URL"),
    project: Optional[str] = typer.Option(None, "--project", help="JIRA project key"),
    base_path: Optional[str] = typer.Option(
        None, "--base-path", help="AITrackdown base path"
    ),
) -> None:
    """Set default adapter and adapter-specific configuration.

    When called without arguments, shows current configuration.
    """
    if not any([adapter, team_key, team_id, owner, repo, server, project, base_path]):
        # Show current configuration
        config = load_config()
        console.print("[bold]Current Configuration:[/bold]")
        console.print(
            f"Default adapter: [cyan]{config.get('default_adapter', 'aitrackdown')}[/cyan]"
        )

        adapters_config = config.get("adapters", {})
        if adapters_config:
            console.print("\n[bold]Adapter Settings:[/bold]")
            for adapter_name, adapter_config in adapters_config.items():
                console.print(f"\n[cyan]{adapter_name}:[/cyan]")
                for key, value in adapter_config.items():
                    # Don't display sensitive values like tokens
                    if (
                        "token" in key.lower()
                        or "key" in key.lower()
                        and "team" not in key.lower()
                    ):
                        value = "***" if value else "not set"
                    console.print(f"  {key}: {value}")
        return

    updates = {}

    # Set default adapter
    if adapter:
        updates["default_adapter"] = adapter.value
        console.print(f"[green]✓[/green] Default adapter set to: {adapter.value}")

    # Build adapter-specific configuration
    adapter_configs = {}

    # Linear configuration
    if team_key or team_id:
        linear_config = {}
        if team_key:
            linear_config["team_key"] = team_key
        if team_id:
            linear_config["team_id"] = team_id
        adapter_configs["linear"] = linear_config
        console.print("[green]✓[/green] Linear settings updated")

    # GitHub configuration
    if owner or repo:
        github_config = {}
        if owner:
            github_config["owner"] = owner
        if repo:
            github_config["repo"] = repo
        adapter_configs["github"] = github_config
        console.print("[green]✓[/green] GitHub settings updated")

    # JIRA configuration
    if server or project:
        jira_config = {}
        if server:
            jira_config["server"] = server
        if project:
            jira_config["project_key"] = project
        adapter_configs["jira"] = jira_config
        console.print("[green]✓[/green] JIRA settings updated")

    # AITrackdown configuration
    if base_path:
        adapter_configs["aitrackdown"] = {"base_path": base_path}
        console.print("[green]✓[/green] AITrackdown settings updated")

    if adapter_configs:
        updates["adapters"] = adapter_configs

    # Merge and save configuration
    if updates:
        config = merge_config(updates)
        save_config(config)
        console.print(f"[dim]Configuration saved to {CONFIG_FILE}[/dim]")


@app.command("configure")
def configure_command(
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
    adapter: Optional[str] = typer.Option(
        None, "--adapter", help="Set default adapter type"
    ),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="Set API key/token"),
    project_id: Optional[str] = typer.Option(
        None, "--project-id", help="Set project ID"
    ),
    team_id: Optional[str] = typer.Option(
        None, "--team-id", help="Set team ID (Linear)"
    ),
    global_scope: bool = typer.Option(
        False,
        "--global",
        "-g",
        help="Save to global config instead of project-specific",
    ),
) -> None:
    """Configure MCP Ticketer integration.

    Run without arguments to launch interactive wizard.
    Use --show to display current configuration.
    Use options to set specific values directly.
    """
    # Show configuration
    if show:
        show_current_config()
        return

    # Direct configuration
    if any([adapter, api_key, project_id, team_id]):
        set_adapter_config(
            adapter=adapter,
            api_key=api_key,
            project_id=project_id,
            team_id=team_id,
            global_scope=global_scope,
        )
        return

    # Run interactive wizard
    configure_wizard()


@app.command("migrate-config")
def migrate_config(
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be done without making changes"
    ),
) -> None:
    """Migrate configuration from old format to new format.

    This command will:
    1. Detect old configuration format
    2. Convert to new schema
    3. Backup old config
    4. Apply new config
    """
    migrate_config_command(dry_run=dry_run)


@app.command("status")
def status_command():
    """Show queue and worker status."""
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
        console.print(
            f"\n[green]● Worker is running[/green] (PID: {worker_status.get('pid')})"
        )
    else:
        console.print("\n[red]○ Worker is not running[/red]")
        if pending > 0:
            console.print(
                "[yellow]Note: There are pending items. Start worker with 'mcp-ticketer worker start'[/yellow]"
            )


@app.command()
def health(
    auto_repair: bool = typer.Option(False, "--auto-repair", help="Attempt automatic repair of issues"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed health information")
) -> None:
    """Check queue system health and detect issues immediately."""

    health_monitor = QueueHealthMonitor()
    health = health_monitor.check_health()

    # Display overall status
    status_color = {
        HealthStatus.HEALTHY: "green",
        HealthStatus.WARNING: "yellow",
        HealthStatus.CRITICAL: "red",
        HealthStatus.FAILED: "red"
    }

    status_icon = {
        HealthStatus.HEALTHY: "✓",
        HealthStatus.WARNING: "⚠️",
        HealthStatus.CRITICAL: "🚨",
        HealthStatus.FAILED: "❌"
    }

    color = status_color.get(health["status"], "white")
    icon = status_icon.get(health["status"], "?")

    console.print(f"[{color}]{icon} Queue Health: {health['status'].upper()}[/{color}]")
    console.print(f"Last checked: {health['timestamp']}")

    # Display alerts
    if health["alerts"]:
        console.print("\n[bold]Issues Found:[/bold]")
        for alert in health["alerts"]:
            alert_color = status_color.get(alert["level"], "white")
            console.print(f"[{alert_color}]  • {alert['message']}[/{alert_color}]")

            if verbose and alert.get("details"):
                for key, value in alert["details"].items():
                    console.print(f"    {key}: {value}")
    else:
        console.print("\n[green]✓ No issues detected[/green]")

    # Auto-repair if requested
    if auto_repair and health["status"] in [HealthStatus.CRITICAL, HealthStatus.WARNING]:
        console.print("\n[yellow]Attempting automatic repair...[/yellow]")
        repair_result = health_monitor.auto_repair()

        if repair_result["actions_taken"]:
            console.print("[green]Repair actions taken:[/green]")
            for action in repair_result["actions_taken"]:
                console.print(f"[green]  ✓ {action}[/green]")

            # Re-check health
            console.print("\n[yellow]Re-checking health after repair...[/yellow]")
            new_health = health_monitor.check_health()
            new_color = status_color.get(new_health["status"], "white")
            new_icon = status_icon.get(new_health["status"], "?")
            console.print(f"[{new_color}]{new_icon} Updated Health: {new_health['status'].upper()}[/{new_color}]")
        else:
            console.print("[yellow]No repair actions available[/yellow]")

    # Exit with appropriate code
    if health["status"] == HealthStatus.CRITICAL:
        raise typer.Exit(1)
    elif health["status"] == HealthStatus.WARNING:
        raise typer.Exit(2)


@app.command()
def create(
    title: str = typer.Argument(..., help="Ticket title"),
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="Ticket description"
    ),
    priority: Priority = typer.Option(
        Priority.MEDIUM, "--priority", "-p", help="Priority level"
    ),
    tags: Optional[list[str]] = typer.Option(
        None, "--tag", "-t", help="Tags (can be specified multiple times)"
    ),
    assignee: Optional[str] = typer.Option(
        None, "--assignee", "-a", help="Assignee username"
    ),
    adapter: Optional[AdapterType] = typer.Option(
        None, "--adapter", help="Override default adapter"
    ),
) -> None:
    """Create a new ticket with comprehensive health checks."""

    # IMMEDIATE HEALTH CHECK - Critical for reliability
    health_monitor = QueueHealthMonitor()
    health = health_monitor.check_health()

    # Display health status
    if health["status"] == HealthStatus.CRITICAL:
        console.print("[red]🚨 CRITICAL: Queue system has serious issues![/red]")
        for alert in health["alerts"]:
            if alert["level"] == "critical":
                console.print(f"[red]  • {alert['message']}[/red]")

        # Attempt auto-repair
        console.print("[yellow]Attempting automatic repair...[/yellow]")
        repair_result = health_monitor.auto_repair()

        if repair_result["actions_taken"]:
            for action in repair_result["actions_taken"]:
                console.print(f"[yellow]  ✓ {action}[/yellow]")

            # Re-check health after repair
            health = health_monitor.check_health()
            if health["status"] == HealthStatus.CRITICAL:
                console.print("[red]❌ Auto-repair failed. Manual intervention required.[/red]")
                console.print("[red]Cannot safely create ticket. Please check system status.[/red]")
                raise typer.Exit(1)
            else:
                console.print("[green]✓ Auto-repair successful. Proceeding with ticket creation.[/green]")
        else:
            console.print("[red]❌ No repair actions available. Manual intervention required.[/red]")
            raise typer.Exit(1)

    elif health["status"] == HealthStatus.WARNING:
        console.print("[yellow]⚠️  Warning: Queue system has minor issues[/yellow]")
        for alert in health["alerts"]:
            if alert["level"] == "warning":
                console.print(f"[yellow]  • {alert['message']}[/yellow]")
        console.print("[yellow]Proceeding with ticket creation...[/yellow]")

    # Get the adapter name with priority: 1) argument, 2) config, 3) .env files, 4) default
    if adapter:
        # Priority 1: Command-line argument - save to config for future use
        adapter_name = adapter.value
        _save_adapter_to_config(adapter_name)
    else:
        # Priority 2: Check existing config
        config = load_config()
        adapter_name = config.get("default_adapter")

        if not adapter_name or adapter_name == "aitrackdown":
            # Priority 3: Check .env files and save if found
            env_adapter = _discover_from_env_files()
            if env_adapter:
                adapter_name = env_adapter
                _save_adapter_to_config(adapter_name)
            else:
                # Priority 4: Default
                adapter_name = "aitrackdown"

    # Create task data
    # Import Priority for type checking
    from ..core.models import Priority as PriorityEnum

    task_data = {
        "title": title,
        "description": description,
        "priority": priority.value if isinstance(priority, PriorityEnum) else priority,
        "tags": tags or [],
        "assignee": assignee,
    }

    # WORKAROUND: Use direct operation for Linear adapter to bypass worker subprocess issue
    if adapter_name == "linear":
        console.print("[yellow]⚠️[/yellow]  Using direct operation for Linear adapter (bypassing queue)")
        try:
            # Load configuration and create adapter directly
            config = load_config()
            adapter_config = config.get("adapters", {}).get(adapter_name, {})

            # Import and create adapter
            from ..core.registry import AdapterRegistry
            adapter = AdapterRegistry.get_adapter(adapter_name, adapter_config)

            # Create task directly
            from ..core.models import Task, Priority
            task = Task(
                title=task_data["title"],
                description=task_data.get("description"),
                priority=Priority(task_data["priority"]) if task_data.get("priority") else Priority.MEDIUM,
                tags=task_data.get("tags", []),
                assignee=task_data.get("assignee")
            )

            # Create ticket synchronously
            import asyncio
            result = asyncio.run(adapter.create(task))

            console.print(f"[green]✓[/green] Ticket created successfully: {result.id}")
            console.print(f"  Title: {result.title}")
            console.print(f"  Priority: {result.priority}")
            console.print(f"  State: {result.state}")
            # Get URL from metadata if available
            if result.metadata and 'linear' in result.metadata and 'url' in result.metadata['linear']:
                console.print(f"  URL: {result.metadata['linear']['url']}")

            return result.id

        except Exception as e:
            console.print(f"[red]❌[/red] Failed to create ticket: {e}")
            raise

    # Use queue for other adapters
    queue = Queue()
    queue_id = queue.add(
        ticket_data=task_data,
        adapter=adapter_name,
        operation="create",
        project_dir=str(Path.cwd())  # Explicitly pass current project directory
    )

    # Register in ticket registry for tracking
    registry = TicketRegistry()
    registry.register_ticket_operation(queue_id, adapter_name, "create", title, task_data)

    console.print(f"[green]✓[/green] Queued ticket creation: {queue_id}")
    console.print(f"  Title: {title}")
    console.print(f"  Priority: {priority}")
    console.print(f"  Adapter: {adapter_name}")
    console.print("[dim]Use 'mcp-ticketer check {queue_id}' to check progress[/dim]")

    # Start worker if needed with immediate feedback
    manager = WorkerManager()
    worker_started = manager.start_if_needed()

    if worker_started:
        console.print("[dim]Worker started to process request[/dim]")

        # Give immediate feedback on processing
        import time
        time.sleep(1)  # Brief pause to let worker start

        # Check if item is being processed
        item = queue.get_item(queue_id)
        if item and item.status == QueueStatus.PROCESSING:
            console.print("[green]✓ Item is being processed by worker[/green]")
        elif item and item.status == QueueStatus.PENDING:
            console.print("[yellow]⏳ Item is queued for processing[/yellow]")
        else:
            console.print("[red]⚠️  Item status unclear - check with 'mcp-ticketer check {queue_id}'[/red]")
    else:
        # Worker didn't start - this is a problem
        pending_count = queue.get_pending_count()
        if pending_count > 1:  # More than just this item
            console.print(f"[red]❌ Worker failed to start with {pending_count} pending items![/red]")
            console.print("[red]This is a critical issue. Try 'mcp-ticketer queue worker start' manually.[/red]")
        else:
            console.print("[yellow]Worker not started (no other pending items)[/yellow]")


@app.command("list")
def list_tickets(
    state: Optional[TicketState] = typer.Option(
        None, "--state", "-s", help="Filter by state"
    ),
    priority: Optional[Priority] = typer.Option(
        None, "--priority", "-p", help="Filter by priority"
    ),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum number of tickets"),
    adapter: Optional[AdapterType] = typer.Option(
        None, "--adapter", help="Override default adapter"
    ),
) -> None:
    """List tickets with optional filters."""

    async def _list():
        adapter_instance = get_adapter(
            override_adapter=adapter.value if adapter else None
        )
        filters = {}
        if state:
            filters["state"] = state
        if priority:
            filters["priority"] = priority
        return await adapter_instance.list(limit=limit, filters=filters)

    tickets = asyncio.run(_list())

    if not tickets:
        console.print("[yellow]No tickets found[/yellow]")
        return

    # Create table
    table = Table(title="Tickets")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title", style="white")
    table.add_column("State", style="green")
    table.add_column("Priority", style="yellow")
    table.add_column("Assignee", style="blue")

    for ticket in tickets:
        # Handle assignee field - Epic doesn't have assignee, Task does
        assignee = getattr(ticket, 'assignee', None) or "-"

        table.add_row(
            ticket.id or "N/A",
            ticket.title,
            ticket.state,
            ticket.priority,
            assignee,
        )

    console.print(table)


@app.command()
def show(
    ticket_id: str = typer.Argument(..., help="Ticket ID"),
    comments: bool = typer.Option(False, "--comments", "-c", help="Show comments"),
    adapter: Optional[AdapterType] = typer.Option(
        None, "--adapter", help="Override default adapter"
    ),
) -> None:
    """Show detailed ticket information."""

    async def _show():
        adapter_instance = get_adapter(
            override_adapter=adapter.value if adapter else None
        )
        ticket = await adapter_instance.read(ticket_id)
        ticket_comments = None
        if comments and ticket:
            ticket_comments = await adapter_instance.get_comments(ticket_id)
        return ticket, ticket_comments

    ticket, ticket_comments = asyncio.run(_show())

    if not ticket:
        console.print(f"[red]✗[/red] Ticket not found: {ticket_id}")
        raise typer.Exit(1)

    # Display ticket details
    console.print(f"\n[bold]Ticket: {ticket.id}[/bold]")
    console.print(f"Title: {ticket.title}")
    console.print(f"State: [green]{ticket.state}[/green]")
    console.print(f"Priority: [yellow]{ticket.priority}[/yellow]")

    if ticket.description:
        console.print("\n[dim]Description:[/dim]")
        console.print(ticket.description)

    if ticket.tags:
        console.print(f"\nTags: {', '.join(ticket.tags)}")

    if ticket.assignee:
        console.print(f"Assignee: {ticket.assignee}")

    # Display comments if requested
    if ticket_comments:
        console.print(f"\n[bold]Comments ({len(ticket_comments)}):[/bold]")
        for comment in ticket_comments:
            console.print(f"\n[dim]{comment.created_at} - {comment.author}:[/dim]")
            console.print(comment.content)


@app.command()
def comment(
    ticket_id: str = typer.Argument(..., help="Ticket ID"),
    content: str = typer.Argument(..., help="Comment content"),
    adapter: Optional[AdapterType] = typer.Option(
        None, "--adapter", help="Override default adapter"
    ),
) -> None:
    """Add a comment to a ticket."""

    async def _comment():
        adapter_instance = get_adapter(
            override_adapter=adapter.value if adapter else None
        )

        # Create comment
        comment = Comment(
            ticket_id=ticket_id,
            content=content,
            author="cli-user"  # Could be made configurable
        )

        result = await adapter_instance.add_comment(comment)
        return result

    try:
        result = asyncio.run(_comment())
        console.print(f"[green]✓[/green] Comment added successfully")
        if result.id:
            console.print(f"Comment ID: {result.id}")
        console.print(f"Content: {content}")
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to add comment: {e}")
        raise typer.Exit(1)


@app.command()
def update(
    ticket_id: str = typer.Argument(..., help="Ticket ID"),
    title: Optional[str] = typer.Option(None, "--title", help="New title"),
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="New description"
    ),
    priority: Optional[Priority] = typer.Option(
        None, "--priority", "-p", help="New priority"
    ),
    assignee: Optional[str] = typer.Option(
        None, "--assignee", "-a", help="New assignee"
    ),
    adapter: Optional[AdapterType] = typer.Option(
        None, "--adapter", help="Override default adapter"
    ),
) -> None:
    """Update ticket fields."""
    updates = {}
    if title:
        updates["title"] = title
    if description:
        updates["description"] = description
    if priority:
        updates["priority"] = (
            priority.value if isinstance(priority, Priority) else priority
        )
    if assignee:
        updates["assignee"] = assignee

    if not updates:
        console.print("[yellow]No updates specified[/yellow]")
        raise typer.Exit(1)

    # Get the adapter name
    config = load_config()
    adapter_name = (
        adapter.value if adapter else config.get("default_adapter", "aitrackdown")
    )

    # Add ticket_id to updates
    updates["ticket_id"] = ticket_id

    # Add to queue with explicit project directory
    queue = Queue()
    queue_id = queue.add(
        ticket_data=updates,
        adapter=adapter_name,
        operation="update",
        project_dir=str(Path.cwd())  # Explicitly pass current project directory
    )

    console.print(f"[green]✓[/green] Queued ticket update: {queue_id}")
    for key, value in updates.items():
        if key != "ticket_id":
            console.print(f"  {key}: {value}")
    console.print("[dim]Use 'mcp-ticketer status {queue_id}' to check progress[/dim]")

    # Start worker if needed
    manager = WorkerManager()
    if manager.start_if_needed():
        console.print("[dim]Worker started to process request[/dim]")


@app.command()
def transition(
    ticket_id: str = typer.Argument(..., help="Ticket ID"),
    state_positional: Optional[TicketState] = typer.Argument(
        None, help="Target state (positional - deprecated, use --state instead)"
    ),
    state: Optional[TicketState] = typer.Option(
        None, "--state", "-s", help="Target state (recommended)"
    ),
    adapter: Optional[AdapterType] = typer.Option(
        None, "--adapter", help="Override default adapter"
    ),
) -> None:
    """Change ticket state with validation.

    Examples:
        # Recommended syntax with flag:
        mcp-ticketer transition BTA-215 --state done
        mcp-ticketer transition BTA-215 -s in_progress

        # Legacy positional syntax (still supported):
        mcp-ticketer transition BTA-215 done

    """
    # Determine which state to use (prefer flag over positional)
    target_state = state if state is not None else state_positional

    if target_state is None:
        console.print("[red]Error: State is required[/red]")
        console.print(
            "Use either:\n"
            "  - Flag syntax (recommended): mcp-ticketer transition TICKET-ID --state STATE\n"
            "  - Positional syntax: mcp-ticketer transition TICKET-ID STATE"
        )
        raise typer.Exit(1)

    # Get the adapter name
    config = load_config()
    adapter_name = (
        adapter.value if adapter else config.get("default_adapter", "aitrackdown")
    )

    # Add to queue with explicit project directory
    queue = Queue()
    queue_id = queue.add(
        ticket_data={
            "ticket_id": ticket_id,
            "state": (
                target_state.value if hasattr(target_state, "value") else target_state
            ),
        },
        adapter=adapter_name,
        operation="transition",
        project_dir=str(Path.cwd())  # Explicitly pass current project directory
    )

    console.print(f"[green]✓[/green] Queued state transition: {queue_id}")
    console.print(f"  Ticket: {ticket_id} → {target_state}")
    console.print("[dim]Use 'mcp-ticketer status {queue_id}' to check progress[/dim]")

    # Start worker if needed
    manager = WorkerManager()
    if manager.start_if_needed():
        console.print("[dim]Worker started to process request[/dim]")


@app.command()
def search(
    query: Optional[str] = typer.Argument(None, help="Search query"),
    state: Optional[TicketState] = typer.Option(None, "--state", "-s"),
    priority: Optional[Priority] = typer.Option(None, "--priority", "-p"),
    assignee: Optional[str] = typer.Option(None, "--assignee", "-a"),
    limit: int = typer.Option(10, "--limit", "-l"),
    adapter: Optional[AdapterType] = typer.Option(
        None, "--adapter", help="Override default adapter"
    ),
) -> None:
    """Search tickets with advanced query."""

    async def _search():
        adapter_instance = get_adapter(
            override_adapter=adapter.value if adapter else None
        )
        search_query = SearchQuery(
            query=query,
            state=state,
            priority=priority,
            assignee=assignee,
            limit=limit,
        )
        return await adapter_instance.search(search_query)

    tickets = asyncio.run(_search())

    if not tickets:
        console.print("[yellow]No tickets found matching query[/yellow]")
        return

    # Display results
    console.print(f"\n[bold]Found {len(tickets)} ticket(s)[/bold]\n")

    for ticket in tickets:
        console.print(f"[cyan]{ticket.id}[/cyan]: {ticket.title}")
        console.print(f"  State: {ticket.state} | Priority: {ticket.priority}")
        if ticket.assignee:
            console.print(f"  Assignee: {ticket.assignee}")
        console.print()


# Add queue command to main app
app.add_typer(queue_app, name="queue")

# Add discover command to main app
app.add_typer(discover_app, name="discover")

# Add diagnostics command
@app.command()
def diagnose(
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Save full report to file"),
    json_output: bool = typer.Option(False, "--json", help="Output report in JSON format"),
    simple: bool = typer.Option(False, "--simple", help="Use simple diagnostics (no heavy dependencies)"),
) -> None:
    """Run comprehensive system diagnostics and health check."""
    if simple:
        from .simple_health import simple_diagnose
        report = simple_diagnose()
        if output_file:
            import json
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            console.print(f"\n📄 Report saved to: {output_file}")
        if json_output:
            import json
            console.print("\n" + json.dumps(report, indent=2))
        if report["issues"]:
            raise typer.Exit(1)
    else:
        try:
            asyncio.run(run_diagnostics(output_file=output_file, json_output=json_output))
        except typer.Exit:
            # typer.Exit is expected - don't fall back to simple diagnostics
            raise
        except Exception as e:
            console.print(f"⚠️  Full diagnostics failed: {e}")
            console.print("🔄 Falling back to simple diagnostics...")
            from .simple_health import simple_diagnose
            report = simple_diagnose()
            if report["issues"]:
                raise typer.Exit(1)


@app.command()
def health() -> None:
    """Quick health check - shows system status summary."""
    from .simple_health import simple_health_check

    result = simple_health_check()
    if result != 0:
        raise typer.Exit(result)

# Create MCP configuration command group
mcp_app = typer.Typer(
    name="mcp",
    help="Configure MCP integration for AI clients (Claude, Gemini, Codex, Auggie)",
    add_completion=False,
)


@app.command()
def check(queue_id: str = typer.Argument(..., help="Queue ID to check")):
    """Check status of a queued operation."""
    queue = Queue()
    item = queue.get_item(queue_id)

    if not item:
        console.print(f"[red]Queue item not found: {queue_id}[/red]")
        raise typer.Exit(1)

    # Display status
    console.print(f"\n[bold]Queue Item: {item.id}[/bold]")
    console.print(f"Operation: {item.operation}")
    console.print(f"Adapter: {item.adapter}")

    # Status with color
    if item.status == QueueStatus.COMPLETED:
        console.print(f"Status: [green]{item.status}[/green]")
    elif item.status == QueueStatus.FAILED:
        console.print(f"Status: [red]{item.status}[/red]")
    elif item.status == QueueStatus.PROCESSING:
        console.print(f"Status: [yellow]{item.status}[/yellow]")
    else:
        console.print(f"Status: {item.status}")

    # Timestamps
    console.print(f"Created: {item.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    if item.processed_at:
        console.print(f"Processed: {item.processed_at.strftime('%Y-%m-%d %H:%M:%S')}")

    # Error or result
    if item.error_message:
        console.print(f"\n[red]Error:[/red] {item.error_message}")
    elif item.result:
        console.print("\n[green]Result:[/green]")
        for key, value in item.result.items():
            console.print(f"  {key}: {value}")

    if item.retry_count > 0:
        console.print(f"\nRetry Count: {item.retry_count}")





@app.command()
def serve(
    adapter: Optional[AdapterType] = typer.Option(
        None, "--adapter", "-a", help="Override default adapter type"
    ),
    base_path: Optional[str] = typer.Option(
        None, "--base-path", help="Base path for AITrackdown adapter"
    ),
):
    """Start MCP server for JSON-RPC communication over stdio.

    This command is used by Claude Code/Desktop when connecting to the MCP server.
    You typically don't need to run this manually - use 'mcp-ticketer mcp' to configure.

    Configuration Resolution:
    - When MCP server starts, it uses the current working directory (cwd)
    - The cwd is set by Claude Code/Desktop from the 'cwd' field in .mcp/config.json
    - Configuration is loaded with this priority:
      1. Project-specific: .mcp-ticketer/config.json in cwd
      2. Global: ~/.mcp-ticketer/config.json
      3. Default: aitrackdown adapter with .aitrackdown base path
    """
    from ..mcp.server import MCPTicketServer

    # Load configuration (respects project-specific config in cwd)
    config = load_config()

    # Determine adapter type with priority: CLI arg > .env files > config > default
    if adapter:
        # Priority 1: Command line argument
        adapter_type = adapter.value
        # Get base config from config file
        adapters_config = config.get("adapters", {})
        adapter_config = adapters_config.get(adapter_type, {})
    else:
        # Priority 2: .env files
        from ..mcp.server import _load_env_configuration
        env_config = _load_env_configuration()
        if env_config:
            adapter_type = env_config["adapter_type"]
            adapter_config = env_config["adapter_config"]
        else:
            # Priority 3: Configuration file
            adapter_type = config.get("default_adapter", "aitrackdown")
            adapters_config = config.get("adapters", {})
            adapter_config = adapters_config.get(adapter_type, {})

    # Override with command line options if provided (highest priority)
    if base_path and adapter_type == "aitrackdown":
        adapter_config["base_path"] = base_path

    # Fallback to legacy config format
    if not adapter_config and "config" in config:
        adapter_config = config["config"]

    # MCP server uses stdio for JSON-RPC, so we can't print to stdout
    # Only print to stderr to avoid interfering with the protocol
    import sys

    if sys.stderr.isatty():
        # Only print if stderr is a terminal (not redirected)
        console.file = sys.stderr
        console.print(f"[green]Starting MCP server[/green] with {adapter_type} adapter")
        console.print(
            "[dim]Server running on stdio. Send JSON-RPC requests via stdin.[/dim]"
        )

    # Create and run server
    try:
        server = MCPTicketServer(adapter_type, adapter_config)
        asyncio.run(server.run())
    except KeyboardInterrupt:
        # Also send this to stderr
        if sys.stderr.isatty():
            console.print("\n[yellow]Server stopped by user[/yellow]")
        if "server" in locals():
            asyncio.run(server.stop())
    except Exception as e:
        # Log error to stderr
        sys.stderr.write(f"MCP server error: {e}\n")
        sys.exit(1)


@mcp_app.command(name="claude")
def mcp_claude(
    global_config: bool = typer.Option(
        False,
        "--global",
        "-g",
        help="Configure Claude Desktop instead of project-level",
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite existing configuration"
    ),
):
    """Configure Claude Code to use mcp-ticketer MCP server.

    Reads configuration from .mcp-ticketer/config.json and updates
    Claude Code's MCP settings accordingly.

    By default, configures project-level (.mcp/config.json).
    Use --global to configure Claude Desktop instead.

    Examples:
        # Configure for current project (default)
        mcp-ticketer mcp claude

        # Configure Claude Desktop globally
        mcp-ticketer mcp claude --global

        # Force overwrite existing configuration
        mcp-ticketer mcp claude --force

    """
    from ..cli.mcp_configure import configure_claude_mcp

    try:
        configure_claude_mcp(global_config=global_config, force=force)
    except Exception as e:
        console.print(f"[red]✗ Configuration failed:[/red] {e}")
        raise typer.Exit(1)


@mcp_app.command(name="gemini")
def mcp_gemini(
    scope: str = typer.Option(
        "project",
        "--scope",
        "-s",
        help="Configuration scope: 'project' (default) or 'user'",
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite existing configuration"
    ),
):
    """Configure Gemini CLI to use mcp-ticketer MCP server.

    Reads configuration from .mcp-ticketer/config.json and creates
    Gemini CLI settings file with mcp-ticketer configuration.

    By default, configures project-level (.gemini/settings.json).
    Use --scope user to configure user-level (~/.gemini/settings.json).

    Examples:
        # Configure for current project (default)
        mcp-ticketer mcp gemini

        # Configure at user level
        mcp-ticketer mcp gemini --scope user

        # Force overwrite existing configuration
        mcp-ticketer mcp gemini --force

    """
    from ..cli.gemini_configure import configure_gemini_mcp

    # Validate scope parameter
    if scope not in ["project", "user"]:
        console.print(
            f"[red]✗ Invalid scope:[/red] '{scope}'. Must be 'project' or 'user'"
        )
        raise typer.Exit(1)

    try:
        configure_gemini_mcp(scope=scope, force=force)  # type: ignore
    except Exception as e:
        console.print(f"[red]✗ Configuration failed:[/red] {e}")
        raise typer.Exit(1)


@mcp_app.command(name="codex")
def mcp_codex(
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite existing configuration"
    ),
):
    """Configure Codex CLI to use mcp-ticketer MCP server.

    Reads configuration from .mcp-ticketer/config.json and creates
    Codex CLI config.toml with mcp-ticketer configuration.

    IMPORTANT: Codex CLI ONLY supports global configuration at ~/.codex/config.toml.
    There is no project-level configuration support. After configuration,
    you must restart Codex CLI for changes to take effect.

    Examples:
        # Configure Codex CLI globally
        mcp-ticketer mcp codex

        # Force overwrite existing configuration
        mcp-ticketer mcp codex --force

    """
    from ..cli.codex_configure import configure_codex_mcp

    try:
        configure_codex_mcp(force=force)
    except Exception as e:
        console.print(f"[red]✗ Configuration failed:[/red] {e}")
        raise typer.Exit(1)


@mcp_app.command(name="auggie")
def mcp_auggie(
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite existing configuration"
    ),
):
    """Configure Auggie CLI to use mcp-ticketer MCP server.

    Reads configuration from .mcp-ticketer/config.json and creates
    Auggie CLI settings.json with mcp-ticketer configuration.

    IMPORTANT: Auggie CLI ONLY supports global configuration at ~/.augment/settings.json.
    There is no project-level configuration support. After configuration,
    you must restart Auggie CLI for changes to take effect.

    Examples:
        # Configure Auggie CLI globally
        mcp-ticketer mcp auggie

        # Force overwrite existing configuration
        mcp-ticketer mcp auggie --force

    """
    from ..cli.auggie_configure import configure_auggie_mcp

    try:
        configure_auggie_mcp(force=force)
    except Exception as e:
        console.print(f"[red]✗ Configuration failed:[/red] {e}")
        raise typer.Exit(1)


# Add command groups to main app (must be after all subcommands are defined)
app.add_typer(linear_app, name="linear")
app.add_typer(mcp_app, name="mcp")


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
