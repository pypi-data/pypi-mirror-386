"""
Unified Server Configuration - Single Source of Truth

This module provides a single, unified configuration source for all server-related settings.
It consolidates the scattered API_* and PB_AGENTS_* variables into a single configuration class
with proper defaults, validation, and type safety.
"""

import os
from typing import Optional

# Load environment variables if dotenv is available
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # If dotenv is not available, just use system environment
    pass


class ServerConfig:
    """Single source of truth for all server configuration."""

    _instance: Optional["ServerConfig"] = None

    def __init__(self):
        """Initialize server configuration with environment variables."""
        # Server host and port configuration
        self.host = os.getenv("HIVE_API_HOST", "0.0.0.0")  # noqa: S104
        port_str = os.getenv("HIVE_API_PORT")
        if not port_str:
            raise ValueError(
                "HIVE_API_PORT environment variable is required. "
                "Please set HIVE_API_PORT in your .env file. See .env.example for reference."
            )
        self.port = int(port_str)
        self.workers = int(os.getenv("HIVE_API_WORKERS", "4"))

        # Environment settings
        self.environment = os.getenv("HIVE_ENVIRONMENT", "development")
        self.log_level = os.getenv("HIVE_LOG_LEVEL", "INFO").upper()
        self.playground_enabled = self._get_bool("HIVE_EMBED_PLAYGROUND", default=True)
        self.playground_mount_path = self._normalize_path(os.getenv("HIVE_PLAYGROUND_MOUNT_PATH", "/playground"))
        self.control_pane_base_url = os.getenv("HIVE_CONTROL_PANE_BASE_URL")

        # Validation
        self._validate_config()

    def _validate_config(self):
        """Validate configuration values."""
        if not (1 <= self.port <= 65535):
            raise ValueError(f"Invalid port number: {self.port}. Must be between 1 and 65535.")

        if self.workers < 1:
            raise ValueError(f"Invalid worker count: {self.workers}. Must be at least 1.")

        if self.environment not in ["development", "staging", "production"]:
            raise ValueError(
                f"Invalid environment: {self.environment}. Must be one of: development, staging, production."
            )

        # Production security validation
        if self.environment == "production":
            import os

            api_key = os.getenv("HIVE_API_KEY")
            if not api_key or api_key.strip() == "" or api_key in ["your-hive-api-key-here"]:
                raise ValueError(
                    "Production environment requires a valid HIVE_API_KEY. "
                    "Set HIVE_API_KEY to a secure value in your environment."
                )

        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            raise ValueError(f"Invalid log level: {self.log_level}. Must be one of: DEBUG, INFO, WARNING, ERROR.")

        if self.control_pane_base_url and not self.control_pane_base_url.startswith(("http://", "https://")):
            raise ValueError("HIVE_CONTROL_PANE_BASE_URL must include http:// or https:// scheme")

    @classmethod
    def get_instance(cls) -> "ServerConfig":
        """Get singleton instance of ServerConfig."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Reset singleton instance (useful for testing)."""
        cls._instance = None

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    def get_base_url(self) -> str:
        """Get the base URL for the server."""
        # Use localhost for local development, otherwise use the configured host
        display_host = "localhost" if self.host in ["0.0.0.0", "::"] else self.host  # noqa: S104
        return f"http://{display_host}:{self.port}"

    def get_playground_url(self) -> str | None:
        """Return the full URL for the embedded Playground if enabled."""
        if not self.playground_enabled:
            return None
        base_url = self.get_base_url()
        return f"{base_url}{self.playground_mount_path}"

    def get_control_pane_url(self) -> str:
        """Return the base URL that the Control Pane should target."""
        return self.control_pane_base_url or self.get_base_url()

    def __repr__(self) -> str:
        """String representation of configuration."""
        return (
            f"ServerConfig(host={self.host}, port={self.port}, workers={self.workers}, environment={self.environment})"
        )

    @staticmethod
    def _get_bool(var_name: str, default: bool) -> bool:
        value = os.getenv(var_name)
        if value is None:
            return default
        return value.strip().lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _normalize_path(path_value: str) -> str:
        if not path_value:
            return "/"
        normalized = path_value if path_value.startswith("/") else f"/{path_value}"
        return normalized.rstrip("/") or "/"


# Global server configuration instance
def get_server_config() -> ServerConfig:
    """Get the global server configuration instance."""
    return ServerConfig.get_instance()


# Convenience functions for common configuration access
def get_server_host() -> str:
    """Get server host."""
    return get_server_config().host


def get_server_port() -> int:
    """Get server port."""
    return get_server_config().port


def get_server_workers() -> int:
    """Get server workers count."""
    return get_server_config().workers


def get_environment() -> str:
    """Get current environment."""
    return get_server_config().environment


def is_development() -> bool:
    """Check if running in development environment."""
    return get_server_config().is_development()


def is_production() -> bool:
    """Check if running in production environment."""
    return get_server_config().is_production()


def get_base_url() -> str:
    """Get the base URL for the server."""
    return get_server_config().get_base_url()


# Export the global instance for direct access
server_config = get_server_config()
