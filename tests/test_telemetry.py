"""
Tests for OpenTelemetry telemetry system.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from claude_monitor.telemetry.event_transformer import OTelTransformer
from claude_monitor.telemetry.models import ClaudeEvent
from claude_monitor.telemetry.models import TelemetryConfig
from claude_monitor.telemetry.otel_setup import initialize_telemetry
from claude_monitor.telemetry.otel_setup import shutdown_telemetry
from claude_monitor.telemetry.session_tracker import SessionTracker


@pytest.fixture
def telemetry_config():
    """Create a test telemetry configuration."""
    return TelemetryConfig(
        service_name="test-claude-monitor",
        use_collector=False,  # Use console exporter for testing
    )


@pytest.fixture
def tracer_and_meter(telemetry_config):
    """Initialize OpenTelemetry for testing."""
    tracer, meter = initialize_telemetry(telemetry_config)
    yield tracer, meter
    shutdown_telemetry()


@pytest.fixture
def transformer(tracer_and_meter):
    """Create an OTelTransformer instance."""
    tracer, meter = tracer_and_meter
    return OTelTransformer(tracer, meter)


@pytest.fixture
def session_tracker(tracer_and_meter):
    """Create a SessionTracker instance."""
    tracer, _ = tracer_and_meter
    return SessionTracker(tracer)


class TestClaudeEvent:
    """Tests for ClaudeEvent model."""

    def test_total_tokens_calculation(self):
        event = ClaudeEvent(
            type="assistant",
            session_id="test-session",
            timestamp=datetime.now(),
            message_id="msg-1",
            tokens_input=100,
            tokens_output=50,
            tokens_cache_creation=25,
            tokens_cache_read=10,
        )

        assert event.total_tokens == 185

    def test_is_tool_event(self):
        tool_use_event = ClaudeEvent(
            type="tool_use",
            session_id="test",
            timestamp=datetime.now(),
            message_id="msg-1",
        )
        assert tool_use_event.is_tool_event()

        message_event = ClaudeEvent(
            type="user",
            session_id="test",
            timestamp=datetime.now(),
            message_id="msg-2",
        )
        assert not message_event.is_tool_event()

    def test_is_message_event(self):
        user_event = ClaudeEvent(
            type="user",
            session_id="test",
            timestamp=datetime.now(),
            message_id="msg-1",
        )
        assert user_event.is_message_event()

        tool_event = ClaudeEvent(
            type="tool_use",
            session_id="test",
            timestamp=datetime.now(),
            message_id="msg-2",
        )
        assert not tool_event.is_message_event()


class TestOTelTransformer:
    """Tests for OTelTransformer."""

    def test_parse_jsonl_line(self, transformer):
        """Test parsing a JSONL line."""
        jsonl = json.dumps(
            {
                "id": "msg-123",
                "type": "user",
                "role": "user",
                "content": "Hello, Claude!",
                "timestamp": "2024-01-30T12:00:00Z",
                "model": "claude-sonnet-4-5",
                "usage": {
                    "input_tokens": 10,
                    "output_tokens": 0,
                },
            }
        )

        event = transformer.parse_jsonl_line(jsonl, "session-123")

        assert event is not None
        assert event.type == "user"
        assert event.session_id == "session-123"
        assert event.message_id == "msg-123"
        assert event.tokens_input == 10
        assert event.model == "claude-sonnet-4-5"

    def test_parse_tool_use_event(self, transformer):
        """Test parsing a tool use event."""
        jsonl = json.dumps(
            {
                "id": "tool-123",
                "type": "tool_use",
                "name": "Read",
                "input": {"file_path": "/test/file.py"},
            }
        )

        event = transformer.parse_jsonl_line(jsonl, "session-123")

        assert event is not None
        assert event.type == "tool_use"
        assert event.tool_name == "Read"
        assert event.tool_input == {"file_path": "/test/file.py"}

    def test_create_span(self, transformer):
        """Test creating a span from an event."""
        event = ClaudeEvent(
            type="user",
            session_id="test-session",
            timestamp=datetime.now(),
            message_id="msg-1",
            tokens_input=100,
            cost_usd=0.01,
            model="claude-sonnet-4-5",
        )

        span = transformer.create_span(event)

        assert span is not None
        # Span will be validated by the SDK

    def test_calculate_cost(self, transformer):
        """Test cost calculation."""
        cost = transformer._calculate_cost(
            input_tokens=1_000_000,  # 1M tokens
            output_tokens=1_000_000,
            cache_creation_tokens=1_000_000,
            cache_read_tokens=1_000_000,
        )

        # Expected: (1M * $3) + (1M * $15) + (1M * $3.75) + (1M * $0.30)
        # = $3 + $15 + $3.75 + $0.30 = $22.05
        assert cost == pytest.approx(22.05, rel=0.01)


class TestSessionTracker:
    """Tests for SessionTracker."""

    def test_start_session(self, session_tracker):
        """Test starting a new session."""
        span = session_tracker.start_session(
            session_id="test-session-1",
            project_path="/test/project",
            session_slug="test-session",
            model="claude-sonnet-4-5",
        )

        assert span is not None
        assert session_tracker.get_session_span("test-session-1") == span

        metadata = session_tracker.get_session_metadata("test-session-1")
        assert metadata is not None
        assert metadata.session_id == "test-session-1"
        assert metadata.is_active

    def test_end_session(self, session_tracker):
        """Test ending a session."""
        session_tracker.start_session("test-session-1")
        session_tracker.end_session("test-session-1")

        metadata = session_tracker.get_session_metadata("test-session-1")
        assert metadata is not None
        assert not metadata.is_active
        assert metadata.end_time is not None

    def test_process_event(self, session_tracker, transformer):
        """Test processing an event."""
        # Start session
        session_tracker.start_session("test-session-1")

        # Create event
        event = ClaudeEvent(
            type="user",
            session_id="test-session-1",
            timestamp=datetime.now(),
            message_id="msg-1",
            tokens_input=100,
            cost_usd=0.01,
        )

        # Create span
        span = transformer.create_span(event)

        # Process event
        session_tracker.process_event(event, span)

        # Check metadata updated
        metadata = session_tracker.get_session_metadata("test-session-1")
        assert metadata.total_messages == 1
        assert metadata.total_tokens == 100
        assert metadata.total_cost == 0.01

    def test_flush_completed_sessions(self, session_tracker):
        """Test flushing old completed sessions."""
        # Start and end a session
        session_tracker.start_session("old-session")
        session_tracker.end_session("old-session")

        # Modify end time to make it old
        metadata = session_tracker.get_session_metadata("old-session")
        metadata.end_time = datetime(2020, 1, 1)

        # Flush
        session_tracker.flush_completed_sessions(max_age_hours=1)

        # Session should be removed
        assert session_tracker.get_session_metadata("old-session") is None


class TestTelemetryConfig:
    """Tests for TelemetryConfig."""

    def test_from_env(self, monkeypatch):
        """Test loading config from environment variables."""
        monkeypatch.setenv("OTEL_SERVICE_NAME", "test-service")
        monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://test:4318")
        monkeypatch.setenv("SPLUNK_HEC_TOKEN", "test-token")
        monkeypatch.setenv("DEPLOYMENT_ENVIRONMENT", "testing")

        config = TelemetryConfig.from_env()

        assert config.service_name == "test-service"
        assert config.collector_endpoint == "http://test:4318"
        assert config.splunk_hec_token == "test-token"
        assert config.deployment_environment == "testing"


@pytest.mark.integration
class TestFileWatcher:
    """Integration tests for file watcher (requires file system)."""

    def test_extract_session_id_from_file(self, transformer, session_tracker):
        """Test extracting session ID from JSONL filename."""
        from claude_monitor.telemetry.file_watcher import ClaudeLogHandler

        handler = ClaudeLogHandler(transformer, session_tracker)

        session_id = handler._extract_session_id(
            "/path/to/logs/abc123-def456-789.jsonl"
        )
        assert session_id == "abc123-def456-789"

    def test_process_file(self, transformer, session_tracker, tmp_path):
        """Test processing a JSONL file."""
        from claude_monitor.telemetry.file_watcher import ClaudeLogHandler

        # Create temp JSONL file
        log_file = tmp_path / "test-session.jsonl"
        events = [
            {
                "id": "msg-1",
                "type": "user",
                "content": "Test message",
                "usage": {"input_tokens": 10},
            },
            {
                "id": "msg-2",
                "type": "assistant",
                "content": "Response",
                "usage": {"output_tokens": 20},
            },
        ]

        with open(log_file, "w") as f:
            for event in events:
                f.write(json.dumps(event) + "\n")

        # Process file
        handler = ClaudeLogHandler(transformer, session_tracker)
        handler._process_file(str(log_file))

        # Verify session was created
        metadata = session_tracker.get_session_metadata("test-session")
        assert metadata is not None
