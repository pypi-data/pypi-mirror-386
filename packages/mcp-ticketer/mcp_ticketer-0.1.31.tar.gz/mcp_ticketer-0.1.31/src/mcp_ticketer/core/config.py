"""Centralized configuration management with caching and validation."""

import json
import logging
import os
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional, Union

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

logger = logging.getLogger(__name__)


class AdapterType(str, Enum):
    """Supported adapter types."""

    GITHUB = "github"
    JIRA = "jira"
    LINEAR = "linear"
    AITRACKDOWN = "aitrackdown"


class BaseAdapterConfig(BaseModel):
    """Base configuration for all adapters."""

    type: AdapterType
    name: Optional[str] = None
    enabled: bool = True
    timeout: float = 30.0
    max_retries: int = 3
    rate_limit: Optional[dict[str, Any]] = None


class GitHubConfig(BaseAdapterConfig):
    """GitHub adapter configuration."""

    type: AdapterType = AdapterType.GITHUB
    token: Optional[str] = Field(None, env="GITHUB_TOKEN")
    owner: Optional[str] = Field(None, env="GITHUB_OWNER")
    repo: Optional[str] = Field(None, env="GITHUB_REPO")
    api_url: str = "https://api.github.com"
    use_projects_v2: bool = False
    custom_priority_scheme: Optional[dict[str, list[str]]] = None

    @field_validator("token", mode="before")
    @classmethod
    def validate_token(cls, v):
        if not v:
            v = os.getenv("GITHUB_TOKEN")
        if not v:
            raise ValueError("GitHub token is required")
        return v

    @field_validator("owner", mode="before")
    @classmethod
    def validate_owner(cls, v):
        if not v:
            v = os.getenv("GITHUB_OWNER")
        if not v:
            raise ValueError("GitHub owner is required")
        return v

    @field_validator("repo", mode="before")
    @classmethod
    def validate_repo(cls, v):
        if not v:
            v = os.getenv("GITHUB_REPO")
        if not v:
            raise ValueError("GitHub repo is required")
        return v


class JiraConfig(BaseAdapterConfig):
    """JIRA adapter configuration."""

    type: AdapterType = AdapterType.JIRA
    server: Optional[str] = Field(None, env="JIRA_SERVER")
    email: Optional[str] = Field(None, env="JIRA_EMAIL")
    api_token: Optional[str] = Field(None, env="JIRA_API_TOKEN")
    project_key: Optional[str] = Field(None, env="JIRA_PROJECT_KEY")
    cloud: bool = True
    verify_ssl: bool = True

    @field_validator("server", mode="before")
    @classmethod
    def validate_server(cls, v):
        if not v:
            v = os.getenv("JIRA_SERVER")
        if not v:
            raise ValueError("JIRA server URL is required")
        return v.rstrip("/")

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, v):
        if not v:
            v = os.getenv("JIRA_EMAIL")
        if not v:
            raise ValueError("JIRA email is required")
        return v

    @field_validator("api_token", mode="before")
    @classmethod
    def validate_api_token(cls, v):
        if not v:
            v = os.getenv("JIRA_API_TOKEN")
        if not v:
            raise ValueError("JIRA API token is required")
        return v


class LinearConfig(BaseAdapterConfig):
    """Linear adapter configuration."""

    type: AdapterType = AdapterType.LINEAR
    api_key: Optional[str] = Field(None, env="LINEAR_API_KEY")
    workspace: Optional[str] = None
    team_key: str
    api_url: str = "https://api.linear.app/graphql"

    @field_validator("api_key", mode="before")
    @classmethod
    def validate_api_key(cls, v):
        if not v:
            v = os.getenv("LINEAR_API_KEY")
        if not v:
            raise ValueError("Linear API key is required")
        return v


class AITrackdownConfig(BaseAdapterConfig):
    """AITrackdown adapter configuration."""

    type: AdapterType = AdapterType.AITRACKDOWN
    # AITrackdown uses local storage, minimal config needed


class QueueConfig(BaseModel):
    """Queue configuration."""

    provider: str = "sqlite"
    connection_string: Optional[str] = None
    batch_size: int = 10
    max_concurrent: int = 5
    retry_attempts: int = 3
    retry_delay: float = 1.0


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: Optional[str] = None
    max_size: str = "10MB"
    backup_count: int = 5


class AppConfig(BaseModel):
    """Main application configuration."""

    adapters: dict[
        str, Union[GitHubConfig, JiraConfig, LinearConfig, AITrackdownConfig]
    ] = {}
    queue: QueueConfig = QueueConfig()
    logging: LoggingConfig = LoggingConfig()
    cache_ttl: int = 300  # Cache TTL in seconds
    default_adapter: Optional[str] = None

    @model_validator(mode="after")
    def validate_adapters(self):
        """Validate adapter configurations."""
        adapters = self.adapters

        if not adapters:
            logger.warning("No adapters configured")
            return self

        # Validate default adapter
        default_adapter = self.default_adapter
        if default_adapter and default_adapter not in adapters:
            raise ValueError(
                f"Default adapter '{default_adapter}' not found in adapters"
            )

        return self

    def get_adapter_config(self, adapter_name: str) -> Optional[BaseAdapterConfig]:
        """Get configuration for a specific adapter."""
        return self.adapters.get(adapter_name)

    def get_enabled_adapters(self) -> dict[str, BaseAdapterConfig]:
        """Get all enabled adapters."""
        return {
            name: config for name, config in self.adapters.items() if config.enabled
        }


class ConfigurationManager:
    """Centralized configuration management with caching and validation."""

    _instance: Optional["ConfigurationManager"] = None
    _config: Optional[AppConfig] = None
    _config_file_paths: list[Path] = []

    def __new__(cls) -> "ConfigurationManager":
        """Singleton pattern for global config access."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize configuration manager."""
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._config_cache: dict[str, Any] = {}
            self._find_config_files()

    def _find_config_files(self) -> None:
        """Find configuration files in project-local directory ONLY.

        SECURITY: This method ONLY searches in the current project directory
        to prevent configuration leakage across projects. It will NEVER read
        from user home directory or system-wide locations.
        """
        # ONLY search in current project directory, never external locations
        possible_paths = [
            Path.cwd() / ".mcp-ticketer" / "config.json",  # Primary JSON config
            Path.cwd() / "mcp-ticketer.yaml",  # Alternative YAML
            Path.cwd() / "mcp-ticketer.yml",  # Alternative YML
            Path.cwd() / "config.yaml",  # Generic YAML
            Path.cwd() / "config.yml",  # Generic YML
        ]

        # Validate all paths are within project (security check)
        validated_paths = []
        for path in possible_paths:
            if path.exists():
                try:
                    if path.resolve().is_relative_to(Path.cwd().resolve()):
                        validated_paths.append(path)
                    else:
                        logger.warning(
                            f"Security: Ignoring config file outside project: {path}"
                        )
                except (ValueError, RuntimeError):
                    # is_relative_to may raise ValueError in some cases
                    # Skip this file if we can't validate it
                    logger.warning(f"Could not validate config file path: {path}")

        self._config_file_paths = validated_paths
        if self._config_file_paths:
            logger.debug(f"Found project-local config files: {self._config_file_paths}")
        else:
            logger.debug("No project-local config files found, will use defaults")

    @lru_cache(maxsize=1)
    def load_config(self, config_file: Optional[Union[str, Path]] = None) -> AppConfig:
        """Load and validate configuration from file and environment.

        Args:
            config_file: Optional specific config file path

        Returns:
            Validated application configuration

        """
        if self._config is not None and config_file is None:
            return self._config

        config_data = {}

        # Load from file
        if config_file:
            config_path = Path(config_file)
            if not config_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {config_path}")
            config_data = self._load_config_file(config_path)
        elif self._config_file_paths:
            # Load from first available config file
            config_data = self._load_config_file(self._config_file_paths[0])
            logger.info(f"Loaded configuration from: {self._config_file_paths[0]}")
        else:
            # No config file found - try environment discovery
            logger.info("No configuration file found, attempting environment discovery")
            config_data = self._discover_from_environment()

        # Parse adapter configurations
        if "adapters" in config_data:
            parsed_adapters = {}
            for name, adapter_config in config_data["adapters"].items():
                adapter_type = adapter_config.get("type", "").lower()

                if adapter_type == "github":
                    parsed_adapters[name] = GitHubConfig(**adapter_config)
                elif adapter_type == "jira":
                    parsed_adapters[name] = JiraConfig(**adapter_config)
                elif adapter_type == "linear":
                    parsed_adapters[name] = LinearConfig(**adapter_config)
                elif adapter_type == "aitrackdown":
                    parsed_adapters[name] = AITrackdownConfig(**adapter_config)
                else:
                    logger.warning(
                        f"Unknown adapter type: {adapter_type} for adapter: {name}"
                    )

            config_data["adapters"] = parsed_adapters

        # Validate and create config
        self._config = AppConfig(**config_data)
        return self._config

    def _load_config_file(self, config_path: Path) -> dict[str, Any]:
        """Load configuration from YAML or JSON file."""
        try:
            with open(config_path, encoding="utf-8") as file:
                if config_path.suffix.lower() in [".yaml", ".yml"]:
                    return yaml.safe_load(file) or {}
                elif config_path.suffix.lower() == ".json":
                    return json.load(file)
                else:
                    # Try YAML first, then JSON
                    content = file.read()
                    try:
                        return yaml.safe_load(content) or {}
                    except yaml.YAMLError:
                        return json.loads(content)
        except Exception as e:
            logger.error(f"Error loading config file {config_path}: {e}")
            return {}

    def _discover_from_environment(self) -> dict[str, Any]:
        """Discover configuration from environment variables."""
        try:
            from .env_discovery import EnvironmentDiscovery

            discovery = EnvironmentDiscovery()
            discovered = discovery.discover_all()

            if not discovered.adapters:
                logger.info("No adapters discovered from environment variables")
                # Return minimal config with aitrackdown as fallback
                return {
                    "adapters": {
                        "aitrackdown": {
                            "type": "aitrackdown",
                            "enabled": True,
                            "base_path": str(Path.home() / ".mcp-ticketer" / ".aitrackdown")
                        }
                    },
                    "default_adapter": "aitrackdown"
                }

            # Convert discovered adapters to config format
            config_data = {
                "adapters": {},
                "default_adapter": None
            }

            for adapter in discovered.adapters:
                adapter_config = {
                    "type": adapter.type.value,
                    "enabled": True
                }

                # Add adapter-specific configuration
                if adapter.type.value == "linear":
                    adapter_config.update({
                        "api_key": adapter.credentials.get("api_key"),
                        "team_id": adapter.credentials.get("team_id"),
                        "project_id": adapter.credentials.get("project_id")
                    })
                elif adapter.type.value == "github":
                    adapter_config.update({
                        "token": adapter.credentials.get("token"),
                        "repo": adapter.credentials.get("repo"),
                        "owner": adapter.credentials.get("owner")
                    })
                elif adapter.type.value == "jira":
                    adapter_config.update({
                        "server": adapter.credentials.get("server"),
                        "email": adapter.credentials.get("email"),
                        "api_token": adapter.credentials.get("api_token"),
                        "project_key": adapter.credentials.get("project_key")
                    })

                config_data["adapters"][adapter.name] = adapter_config

                # Set first discovered adapter as default
                if config_data["default_adapter"] is None:
                    config_data["default_adapter"] = adapter.name

            logger.info(f"Discovered {len(config_data['adapters'])} adapter(s) from environment")
            return config_data

        except ImportError:
            logger.warning("Environment discovery not available, using aitrackdown fallback")
            return {
                "adapters": {
                    "aitrackdown": {
                        "type": "aitrackdown",
                        "enabled": True,
                        "base_path": str(Path.home() / ".mcp-ticketer" / ".aitrackdown")
                    }
                },
                "default_adapter": "aitrackdown"
            }
        except Exception as e:
            logger.error(f"Environment discovery failed: {e}")
            return {
                "adapters": {
                    "aitrackdown": {
                        "type": "aitrackdown",
                        "enabled": True,
                        "base_path": str(Path.home() / ".mcp-ticketer" / ".aitrackdown")
                    }
                },
                "default_adapter": "aitrackdown"
            }

    def get_config(self) -> AppConfig:
        """Get the current configuration."""
        if self._config is None:
            return self.load_config()
        return self._config

    def get_adapter_config(self, adapter_name: str) -> Optional[BaseAdapterConfig]:
        """Get configuration for a specific adapter."""
        config = self.get_config()
        return config.get_adapter_config(adapter_name)

    def get_enabled_adapters(self) -> dict[str, BaseAdapterConfig]:
        """Get all enabled adapter configurations."""
        config = self.get_config()
        return config.get_enabled_adapters()

    def get_queue_config(self) -> QueueConfig:
        """Get queue configuration."""
        config = self.get_config()
        return config.queue

    def get_logging_config(self) -> LoggingConfig:
        """Get logging configuration."""
        config = self.get_config()
        return config.logging

    def reload_config(
        self, config_file: Optional[Union[str, Path]] = None
    ) -> AppConfig:
        """Reload configuration from file."""
        # Clear cache
        self.load_config.cache_clear()
        self._config = None
        self._config_cache.clear()

        # Reload
        return self.load_config(config_file)

    def set_config_value(self, key: str, value: Any) -> None:
        """Set a configuration value (for testing/runtime overrides)."""
        self._config_cache[key] = value

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get a configuration value with caching."""
        if key in self._config_cache:
            return self._config_cache[key]

        # Parse nested keys like "queue.batch_size"
        config = self.get_config()
        parts = key.split(".")
        value = config.dict()

        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default

        self._config_cache[key] = value
        return value

    def create_sample_config(self, output_path: Union[str, Path]) -> None:
        """Create a sample configuration file."""
        sample_config = {
            "adapters": {
                "github-main": {
                    "type": "github",
                    "token": "${GITHUB_TOKEN}",
                    "owner": "your-org",
                    "repo": "your-repo",
                    "enabled": True,
                },
                "linear-dev": {
                    "type": "linear",
                    "api_key": "${LINEAR_API_KEY}",
                    "team_key": "DEV",
                    "enabled": True,
                },
                "jira-support": {
                    "type": "jira",
                    "server": "https://your-org.atlassian.net",
                    "email": "${JIRA_EMAIL}",
                    "api_token": "${JIRA_API_TOKEN}",
                    "project_key": "SUPPORT",
                    "enabled": False,
                },
            },
            "queue": {"provider": "sqlite", "batch_size": 10, "max_concurrent": 5},
            "logging": {"level": "INFO", "file": "mcp-ticketer.log"},
            "default_adapter": "github-main",
        }

        output_path = Path(output_path)
        with open(output_path, "w", encoding="utf-8") as file:
            yaml.dump(sample_config, file, default_flow_style=False, indent=2)

        logger.info(f"Sample configuration created at: {output_path}")


# Global configuration manager instance
config_manager = ConfigurationManager()


def get_config() -> AppConfig:
    """Get the global configuration."""
    return config_manager.get_config()


def get_adapter_config(adapter_name: str) -> Optional[BaseAdapterConfig]:
    """Get configuration for a specific adapter."""
    return config_manager.get_adapter_config(adapter_name)


def reload_config(config_file: Optional[Union[str, Path]] = None) -> AppConfig:
    """Reload the global configuration."""
    return config_manager.reload_config(config_file)
