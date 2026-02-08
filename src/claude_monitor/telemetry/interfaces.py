"""
OpenTelemetry Telemetry Interfaces and Protocols.

This module defines the contracts for telemetry components, enabling:
- Dependency injection
- Easy testing with mocks
- Plugin architecture for exporters
- Type-safe implementations

Design Philosophy:
- Protocol over ABC for structural subtyping
- Clear separation of concerns (SRP)
- Open for extension, closed for modification (OCP)
"""

from __future__ import annotations

from typing import Any
from typing import Dict
from typing import Optional
from typing import Protocol
from typing import runtime_checkable

from opentelemetry import metrics
from opentelemetry import trace

from claude_monitor.telemetry.models import ClaudeEvent
from claude_monitor.telemetry.models import SessionMetadata


@runtime_checkable
class EventTransformer(Protocol):
    """
    Protocol for transforming Claude Code events into OpenTelemetry signals.

    Implementations must handle:
    - Parsing JSONL event data
    - Creating OTel spans with proper attributes
    - Recording metrics
    - Following OTel semantic conventions
    """

    def parse_jsonl_line(
        self, line: str, session_id: str
    ) -> Optional[ClaudeEvent]:
        """
        Parse a single JSONL line into a ClaudeEvent.

        Args:
            line: Raw JSONL string
            session_id: Session identifier from filename

        Returns:
            Parsed ClaudeEvent or None if parsing fails
        """
        ...

    def create_span(
        self,
        event: ClaudeEvent,
        parent_context: Optional[trace.Context] = None,
    ) -> trace.Span:
        """
        Create an OpenTelemetry span for a Claude event.

        Args:
            event: Parsed Claude event
            parent_context: Optional parent span context for hierarchy

        Returns:
            OpenTelemetry span with attributes set
        """
        ...

    def record_metrics(self, event: ClaudeEvent) -> None:
        """
        Record metrics for a Claude event.

        Args:
            event: The Claude event to record metrics for
        """
        ...


@runtime_checkable
class SessionTracker(Protocol):
    """
    Protocol for tracking Claude Code sessions and managing span lifecycle.

    Responsibilities:
    - Managing root spans for sessions
    - Tracking session metadata and aggregates
    - Handling parent-child span relationships
    """

    def start_session(
        self,
        session_id: str,
        project_path: str = "",
        session_slug: str = "",
        model: Optional[str] = None,
    ) -> trace.Span:
        """
        Start tracking a new session.

        Args:
            session_id: Unique session identifier
            project_path: Project working directory
            session_slug: Human-readable session name
            model: Model name

        Returns:
            Root span for the session
        """
        ...

    def end_session(self, session_id: str) -> None:
        """
        End a session and close its root span.

        Args:
            session_id: Session identifier
        """
        ...

    def process_event(self, event: ClaudeEvent, span: trace.Span) -> None:
        """
        Process an event and update session metadata.

        Args:
            event: The Claude event
            span: The span created for this event
        """
        ...

    def get_session_span(self, session_id: str) -> Optional[trace.Span]:
        """
        Get the root span for a session.

        Args:
            session_id: Session identifier

        Returns:
            Root span or None if session not found
        """
        ...

    def get_session_metadata(
        self, session_id: str
    ) -> Optional[SessionMetadata]:
        """
        Get metadata for a session.

        Args:
            session_id: Session identifier

        Returns:
            SessionMetadata or None if session not found
        """
        ...


@runtime_checkable
class TelemetryExporter(Protocol):
    """
    Protocol for telemetry exporters.

    This enables pluggable backends (Splunk, Dynatrace, Langfuse, etc.)
    Each exporter is responsible for:
    - Configuring its specific backend
    - Validating configuration
    - Providing health checks
    - Graceful error handling
    """

    @property
    def name(self) -> str:
        """Exporter name (e.g., 'splunk', 'dynatrace', 'langfuse')."""
        ...

    @property
    def enabled(self) -> bool:
        """Whether this exporter is enabled."""
        ...

    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the exporter with backend-specific settings.

        Args:
            config: Configuration dictionary

        Raises:
            ValueError: If configuration is invalid
        """
        ...

    def get_span_processor(self) -> trace.SpanProcessor:
        """
        Get the span processor for this exporter.

        Returns:
            Configured SpanProcessor instance
        """
        ...

    def get_metric_reader(self) -> metrics.MetricReader:
        """
        Get the metric reader for this exporter.

        Returns:
            Configured MetricReader instance
        """
        ...

    def validate_config(self) -> bool:
        """
        Validate exporter configuration.

        Returns:
            True if configuration is valid

        Raises:
            ValueError: If configuration is invalid with details
        """
        ...

    def health_check(self) -> bool:
        """
        Check if exporter backend is reachable.

        Returns:
            True if healthy, False otherwise
        """
        ...

    def shutdown(self) -> None:
        """Gracefully shutdown the exporter."""
        ...


@runtime_checkable
class FileWatcher(Protocol):
    """
    Protocol for watching Claude Code log files.

    Responsibilities:
    - Monitoring filesystem for changes
    - Processing new JSONL lines
    - Handling file creation/modification events
    """

    def start(self) -> None:
        """Start watching for file changes."""
        ...

    def stop(self) -> None:
        """Stop watching for file changes."""
        ...

    def is_running(self) -> bool:
        """Check if watcher is running."""
        ...


@runtime_checkable
class ConfigurationProvider(Protocol):
    """
    Protocol for configuration providers.

    Enables different configuration sources:
    - Environment variables
    - Configuration files (YAML, TOML)
    - Command-line arguments
    - Remote configuration servers
    """

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            key: Configuration key (dot-notation supported)
            default: Default value if key not found

        Returns:
            Configuration value
        """
        ...

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value.

        Args:
            key: Configuration key
            value: Configuration value
        """
        ...

    def reload(self) -> None:
        """Reload configuration from source."""
        ...

    def validate(self) -> bool:
        """
        Validate configuration.

        Returns:
            True if valid

        Raises:
            ValueError: If invalid with details
        """
        ...
