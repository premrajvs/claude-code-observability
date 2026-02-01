"""
Data models for OpenTelemetry telemetry.
"""

from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from typing import Any
from typing import Dict
from typing import Optional


@dataclass
class ClaudeEvent:
    """Represents a single event from Claude Code JSONL logs."""

    type: str  # user, assistant, tool_use, tool_result, etc.
    session_id: str
    timestamp: datetime
    message_id: str
    request_id: Optional[str] = None

    # Token usage
    tokens_input: int = 0
    tokens_output: int = 0
    tokens_cache_creation: int = 0
    tokens_cache_read: int = 0

    # Cost
    cost_usd: float = 0.0

    # Model info
    model: Optional[str] = None

    # Tool info (for tool_use events)
    tool_name: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None

    # Tool result info
    tool_result: Optional[Any] = None
    tool_error: Optional[str] = None

    # Message content
    content: Optional[str] = None

    # Session metadata
    project_path: Optional[str] = None
    session_slug: Optional[str] = None

    # Raw event data
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        """Calculate total tokens."""
        return (
            self.tokens_input
            + self.tokens_output
            + self.tokens_cache_creation
            + self.tokens_cache_read
        )

    def is_tool_event(self) -> bool:
        """Check if this is a tool-related event."""
        return self.type in ("tool_use", "tool_result")

    def is_message_event(self) -> bool:
        """Check if this is a message event."""
        return self.type in ("user", "assistant")


@dataclass
class SessionMetadata:
    """Metadata about a Claude Code session."""

    session_id: str
    project_path: str
    session_slug: str
    start_time: datetime
    end_time: Optional[datetime] = None

    # Aggregated metrics
    total_messages: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0

    # Tool usage stats
    tools_used: Dict[str, int] = field(default_factory=dict)

    # Model info
    model: Optional[str] = None

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate session duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def is_active(self) -> bool:
        """Check if session is still active."""
        return self.end_time is None


@dataclass
class TelemetryConfig:
    """Configuration for telemetry collection."""

    # Service identification
    service_name: str = "claude-monitor"
    service_version: str = "1.0.0"
    deployment_environment: str = "local"

    # Export mode
    use_collector: bool = True  # True = OTLP to collector, False = direct to backend
    collector_endpoint: str = "http://localhost:4318"  # OTLP HTTP endpoint

    # Splunk HEC (for direct mode)
    splunk_hec_token: Optional[str] = None
    splunk_hec_url: Optional[str] = None
    splunk_index: str = "main"
    splunk_source: str = "claude-monitor"
    splunk_sourcetype: str = "_json"

    # Sampling
    trace_sample_rate: float = 1.0  # 1.0 = 100% sampling

    # Batch processing
    batch_timeout_seconds: int = 10
    batch_max_size: int = 100

    # File watching
    watch_directory: Optional[str] = None  # Will default to ~/.claude/projects
    file_check_interval_seconds: float = 1.0

    @classmethod
    def from_env(cls) -> "TelemetryConfig":
        """Create configuration from environment variables."""
        import os

        return cls(
            service_name=os.getenv("OTEL_SERVICE_NAME", "claude-monitor"),
            collector_endpoint=os.getenv(
                "OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318"
            ),
            splunk_hec_token=os.getenv("SPLUNK_HEC_TOKEN"),
            splunk_hec_url=os.getenv("SPLUNK_HEC_URL"),
            deployment_environment=os.getenv("DEPLOYMENT_ENVIRONMENT", "local"),
            use_collector=os.getenv("TELEMETRY_USE_COLLECTOR", "true").lower()
            == "true",
        )
