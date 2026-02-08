"""
OpenTelemetry-based telemetry collection for Claude Code conversations.

This module provides components to:
- Watch Claude Code log files
- Transform JSONL events to OpenTelemetry signals
- Export traces, metrics, and logs to backends (Splunk, Dynatrace, etc.)
"""

from claude_monitor.telemetry.event_transformer import ClaudeEvent
from claude_monitor.telemetry.event_transformer import OTelTransformer
from claude_monitor.telemetry.file_watcher import ClaudeLogWatcher
from claude_monitor.telemetry.otel_setup import initialize_telemetry
from claude_monitor.telemetry.otel_setup import shutdown_telemetry
from claude_monitor.telemetry.session_tracker import SessionTracker


__all__ = [
    "ClaudeEvent",
    "OTelTransformer",
    "ClaudeLogWatcher",
    "SessionTracker",
    "initialize_telemetry",
    "shutdown_telemetry",
]
