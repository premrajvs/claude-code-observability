"""
Enterprise-Grade Configuration Management for Claude Code Observatory.

This module provides robust configuration with:
- Type-safe validation (Pydantic)
- Environment variable support
- Multiple configuration sources (env, file, defaults)
- Configuration validation and error reporting
- Hot-reload capability

Design Philosophy:
- Fail-fast: Invalid config caught at startup
- Explicit over implicit: No hidden defaults
- Secure by default: Secrets from environment only
- Well-documented: Every field has description
"""

import os
from enum import Enum
from pathlib import Path
from typing import Dict
from typing import List
from typing import Optional

from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class LogLevel(str, Enum):
    """Logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ExportMode(str, Enum):
    """Telemetry export mode."""

    COLLECTOR = "collector"  # Via OpenTelemetry Collector (recommended)
    DIRECT = "direct"  # Direct to backend (advanced)
    CONSOLE = "console"  # Console output (debugging)
    FILE = "file"  # File output (debugging)


class ExporterConfig(BaseSettings):
    """
    Configuration for a single exporter.

    Each exporter can have custom settings while sharing common structure.
    """

    model_config = SettingsConfigDict(
        env_prefix="EXPORTER_",
        case_sensitive=False,
        extra="allow",  # Allow backend-specific fields
    )

    name: str = Field(
        description="Exporter name (splunk, dynatrace, langfuse, etc.)"
    )

    enabled: bool = Field(
        default=True, description="Whether this exporter is enabled"
    )

    # Backend-specific config stored in this dict
    config: Dict[str, str] = Field(
        default_factory=dict,
        description="Backend-specific configuration (tokens, URLs, etc.)",
    )


class TelemetryConfig(BaseSettings):
    """
    Complete telemetry configuration with validation.

    This is the single source of truth for all telemetry settings.
    Loads from environment variables, config files, or defaults.

    Environment Variable Mapping:
        OTEL_SERVICE_NAME → service_name
        OTEL_SERVICE_VERSION → service_version
        OTEL_EXPORTER_OTLP_ENDPOINT → collector_endpoint
        CLAUDE_WATCH_DIRECTORY → watch_directory
    """

    model_config = SettingsConfigDict(
        env_prefix="OTEL_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ===== Service Identification =====
    service_name: str = Field(
        default="claude-code-observatory",
        description="Service name for OpenTelemetry resource",
        alias="SERVICE_NAME",
    )

    service_version: str = Field(
        default="1.0.0",
        description="Service version",
        alias="SERVICE_VERSION",
    )

    deployment_environment: str = Field(
        default="local",
        description="Deployment environment (local, dev, staging, prod)",
        alias="DEPLOYMENT_ENVIRONMENT",
    )

    # ===== Export Configuration =====
    export_mode: ExportMode = Field(
        default=ExportMode.COLLECTOR,
        description="Telemetry export mode",
    )

    collector_endpoint: str = Field(
        default="http://localhost:4318",
        description="OpenTelemetry Collector OTLP HTTP endpoint",
        alias="EXPORTER_OTLP_ENDPOINT",
    )

    # ===== Batch & Performance =====
    batch_timeout_seconds: int = Field(
        default=10,
        ge=1,
        le=60,
        description="Batch timeout in seconds (1-60)",
    )

    batch_max_size: int = Field(
        default=512,
        ge=1,
        le=10000,
        description="Maximum batch size (1-10000)",
    )

    # ===== Sampling =====
    trace_sample_rate: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Trace sampling rate (0.0-1.0, 1.0=100%)",
    )

    # ===== File Watching =====
    watch_directory: Optional[str] = Field(
        default=None,
        description="Directory to watch for Claude Code logs (default: ~/.claude/projects)",
    )

    file_check_interval_seconds: float = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        description="File check interval in seconds (0.1-10.0)",
    )

    # ===== Logging =====
    log_level: LogLevel = Field(
        default=LogLevel.INFO, description="Logging level"
    )

    enable_debug_logging: bool = Field(
        default=False, description="Enable debug logging for troubleshooting"
    )

    # ===== Multiple Exporters (Advanced) =====
    exporters: List[ExporterConfig] = Field(
        default_factory=list,
        description="List of exporter configurations (for direct mode)",
    )

    # ===== Feature Flags =====
    enable_metrics: bool = Field(
        default=True, description="Enable metrics collection"
    )

    enable_traces: bool = Field(
        default=True, description="Enable trace collection"
    )

    enable_logs: bool = Field(
        default=False,
        description="Enable log collection (experimental)",
    )

    # ===== Advanced =====
    max_attribute_length: int = Field(
        default=4000,
        ge=100,
        le=50000,
        description="Maximum span attribute length (100-50000)",
    )

    enable_span_events: bool = Field(
        default=True,
        description="Use span events for large content (recommended)",
    )

    @field_validator("watch_directory")
    @classmethod
    def set_default_watch_directory(
        cls, v: Optional[str]
    ) -> str:
        """Set default watch directory if not provided."""
        if v is None:
            home = Path.home()
            return str(home / ".claude" / "projects")
        return v

    @field_validator("collector_endpoint")
    @classmethod
    def validate_collector_endpoint(cls, v: str) -> str:
        """Validate collector endpoint URL."""
        if not v.startswith(("http://", "https://")):
            raise ValueError(
                f"Collector endpoint must start with http:// or https://, got: {v}"
            )
        return v.rstrip("/")  # Remove trailing slash

    @model_validator(mode="after")
    def validate_export_mode(self) -> "TelemetryConfig":
        """Validate configuration based on export mode."""
        if self.export_mode == ExportMode.DIRECT:
            if not self.exporters:
                raise ValueError(
                    "Direct export mode requires at least one exporter configured"
                )

        if self.export_mode == ExportMode.COLLECTOR:
            if not self.collector_endpoint:
                raise ValueError(
                    "Collector mode requires collector_endpoint to be set"
                )

        return self

    @classmethod
    def from_env(cls) -> "TelemetryConfig":
        """
        Create configuration from environment variables.

        Reads from:
        1. Environment variables (OTEL_*)
        2. .env file if present
        3. Default values

        Returns:
            Validated TelemetryConfig instance

        Raises:
            ValidationError: If configuration is invalid
        """
        return cls()

    @classmethod
    def from_dict(cls, config_dict: Dict) -> "TelemetryConfig":
        """
        Create configuration from dictionary.

        Args:
            config_dict: Configuration dictionary

        Returns:
            Validated TelemetryConfig instance
        """
        return cls(**config_dict)

    def to_dict(self) -> Dict:
        """
        Export configuration as dictionary.

        Returns:
            Configuration dictionary (excluding secrets)
        """
        return self.model_dump(exclude={"exporters"})

    def validate_paths(self) -> None:
        """
        Validate that configured paths exist.

        Raises:
            FileNotFoundError: If watch_directory doesn't exist
        """
        watch_path = Path(self.watch_directory)
        if not watch_path.exists():
            raise FileNotFoundError(
                f"Watch directory does not exist: {watch_path}"
            )

        if not watch_path.is_dir():
            raise ValueError(
                f"Watch directory is not a directory: {watch_path}"
            )

    def __repr__(self) -> str:
        """String representation (safe - no secrets)."""
        return (
            f"TelemetryConfig("
            f"service={self.service_name}, "
            f"mode={self.export_mode}, "
            f"endpoint={self.collector_endpoint}, "
            f"watch={self.watch_directory})"
        )


# Convenience function for loading configuration
def load_config(
    validate_paths: bool = True,
    config_dict: Optional[Dict] = None,
) -> TelemetryConfig:
    """
    Load and validate telemetry configuration.

    Args:
        validate_paths: Whether to validate filesystem paths
        config_dict: Optional configuration dictionary to override env

    Returns:
        Validated TelemetryConfig

    Raises:
        ValidationError: If configuration is invalid
        FileNotFoundError: If paths don't exist (when validate_paths=True)

    Example:
        config = load_config()
        print(f"Watching: {config.watch_directory}")
        print(f"Sending to: {config.collector_endpoint}")
    """
    if config_dict:
        config = TelemetryConfig.from_dict(config_dict)
    else:
        config = TelemetryConfig.from_env()

    if validate_paths:
        config.validate_paths()

    return config
