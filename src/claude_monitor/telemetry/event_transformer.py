"""
Transform Claude Code JSONL events into OpenTelemetry signals.
"""

import json
import logging
from datetime import datetime
from typing import Any
from typing import Dict
from typing import Optional

from opentelemetry import metrics
from opentelemetry import trace
from opentelemetry.trace import Status
from opentelemetry.trace import StatusCode

from claude_monitor.telemetry.models import ClaudeEvent


logger = logging.getLogger(__name__)


class OTelTransformer:
    """
    Transforms Claude Code events into OpenTelemetry traces, metrics, and logs.
    """

    def __init__(self, tracer: trace.Tracer, meter: metrics.Meter):
        self.tracer = tracer
        self.meter = meter

        # Create metrics
        self._create_metrics()

    def _create_metrics(self):
        """Create OpenTelemetry metrics."""
        # Token metrics
        self.tokens_input_counter = self.meter.create_counter(
            "claude.tokens.input",
            description="Total input tokens",
            unit="tokens",
        )

        self.tokens_output_counter = self.meter.create_counter(
            "claude.tokens.output",
            description="Total output tokens",
            unit="tokens",
        )

        self.tokens_cache_creation_counter = self.meter.create_counter(
            "claude.tokens.cache_creation",
            description="Cache creation tokens",
            unit="tokens",
        )

        self.tokens_cache_read_counter = self.meter.create_counter(
            "claude.tokens.cache_read",
            description="Cache read tokens",
            unit="tokens",
        )

        self.tokens_total_counter = self.meter.create_counter(
            "claude.tokens.total",
            description="Total tokens (all types)",
            unit="tokens",
        )

        # Cost metrics
        self.cost_counter = self.meter.create_counter(
            "claude.cost.total",
            description="Total cost in USD",
            unit="USD",
        )

        # Message count
        self.message_counter = self.meter.create_counter(
            "claude.messages.count",
            description="Number of messages",
            unit="messages",
        )

        # Tool usage
        self.tool_usage_counter = self.meter.create_counter(
            "claude.tools.usage",
            description="Tool usage count",
            unit="tools",
        )

    def parse_jsonl_line(self, line: str, session_id: str) -> Optional[ClaudeEvent]:
        """
        Parse a single JSONL line into a ClaudeEvent.

        Args:
            line: JSONL line to parse
            session_id: Session ID from the filename

        Returns:
            ClaudeEvent or None if parsing fails
        """
        try:
            data = json.loads(line.strip())
            return self._parse_event(data, session_id)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSONL line: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing event: {e}", exc_info=True)
            return None

    def _parse_event(self, data: Dict[str, Any], session_id: str) -> ClaudeEvent:
        """Parse raw JSON data into ClaudeEvent."""
        # Determine event type
        event_type = self._determine_event_type(data)

        # Parse timestamp
        timestamp = self._parse_timestamp(data.get("timestamp"))

        # Extract token usage
        usage = data.get("usage", {})
        tokens_input = usage.get("input_tokens", 0)
        tokens_output = usage.get("output_tokens", 0)
        tokens_cache_creation = usage.get("cache_creation_input_tokens", 0)
        tokens_cache_read = usage.get("cache_read_input_tokens", 0)

        # Calculate cost (simplified - should use actual pricing)
        cost_usd = self._calculate_cost(
            tokens_input, tokens_output, tokens_cache_creation, tokens_cache_read
        )

        # Extract tool information
        tool_name = None
        tool_input = None
        tool_result = None
        tool_error = None

        if event_type == "tool_use":
            tool_name = data.get("name")
            tool_input = data.get("input")
        elif event_type == "tool_result":
            tool_result = data.get("content")
            if isinstance(tool_result, list) and tool_result:
                # Check for error in tool result
                first_item = tool_result[0]
                if isinstance(first_item, dict) and first_item.get("type") == "error":
                    tool_error = first_item.get("error")

        # Extract content
        content = None
        if "content" in data:
            content = self._extract_content(data["content"])

        return ClaudeEvent(
            type=event_type,
            session_id=session_id,
            timestamp=timestamp,
            message_id=data.get("id", ""),
            request_id=data.get("request_id"),
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            tokens_cache_creation=tokens_cache_creation,
            tokens_cache_read=tokens_cache_read,
            cost_usd=cost_usd,
            model=data.get("model"),
            tool_name=tool_name,
            tool_input=tool_input,
            tool_result=tool_result,
            tool_error=tool_error,
            content=content,
            raw_data=data,
        )

    def _determine_event_type(self, data: Dict[str, Any]) -> str:
        """Determine the type of event from raw data."""
        if "type" in data:
            return data["type"]

        # Infer from role
        role = data.get("role", "")
        if role == "user":
            return "user"
        elif role == "assistant":
            return "assistant"

        return "unknown"

    def _parse_timestamp(self, timestamp_str: Optional[str]) -> datetime:
        """Parse timestamp string to datetime."""
        if not timestamp_str:
            return datetime.now()

        try:
            # Try ISO format
            return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return datetime.now()

    def _calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        cache_creation_tokens: int,
        cache_read_tokens: int,
    ) -> float:
        """
        Calculate cost based on token usage.

        Note: This is a simplified calculation. Real pricing varies by model.
        Claude Sonnet 4.5 pricing (as of example):
        - Input: $3 per million tokens
        - Output: $15 per million tokens
        - Cache creation: $3.75 per million tokens
        - Cache read: $0.30 per million tokens
        """
        input_cost = (input_tokens / 1_000_000) * 3.0
        output_cost = (output_tokens / 1_000_000) * 15.0
        cache_creation_cost = (cache_creation_tokens / 1_000_000) * 3.75
        cache_read_cost = (cache_read_tokens / 1_000_000) * 0.30

        return input_cost + output_cost + cache_creation_cost + cache_read_cost

    def _extract_content(self, content: Any) -> Optional[str]:
        """Extract text content from various content formats."""
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            # Extract text from content blocks
            text_parts = []
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                elif isinstance(item, str):
                    text_parts.append(item)
            return "\n".join(text_parts)

        if isinstance(content, dict):
            return content.get("text")

        return None

    def create_span(
        self,
        event: ClaudeEvent,
        parent_context: Optional[trace.Context] = None,
    ) -> trace.Span:
        """
        Create an OpenTelemetry span for a Claude event.

        Args:
            event: The Claude event
            parent_context: Optional parent span context

        Returns:
            OpenTelemetry span
        """
        # Determine span name
        span_name = self._get_span_name(event)

        # Create span
        span = self.tracer.start_span(
            span_name,
            context=parent_context,
            start_time=int(event.timestamp.timestamp() * 1e9),  # nanoseconds
        )

        # Set attributes
        span.set_attribute("session.id", event.session_id)
        span.set_attribute("message.id", event.message_id)
        span.set_attribute("message.type", event.type)

        if event.request_id:
            span.set_attribute("request.id", event.request_id)

        if event.model:
            span.set_attribute("model", event.model)

        # Token attributes
        if event.tokens_input > 0:
            span.set_attribute("tokens.input", event.tokens_input)
        if event.tokens_output > 0:
            span.set_attribute("tokens.output", event.tokens_output)
        if event.tokens_cache_creation > 0:
            span.set_attribute("tokens.cache_creation", event.tokens_cache_creation)
        if event.tokens_cache_read > 0:
            span.set_attribute("tokens.cache_read", event.tokens_cache_read)

        span.set_attribute("tokens.total", event.total_tokens)

        # Cost
        if event.cost_usd > 0:
            span.set_attribute("cost.usd", event.cost_usd)

        # Tool attributes
        if event.tool_name:
            span.set_attribute("tool.name", event.tool_name)

        # Set status based on errors
        if event.tool_error:
            span.set_status(Status(StatusCode.ERROR, event.tool_error))
        else:
            span.set_status(Status(StatusCode.OK))

        return span

    def _get_span_name(self, event: ClaudeEvent) -> str:
        """Generate span name from event."""
        if event.type == "tool_use" and event.tool_name:
            return f"tool.{event.tool_name}"
        elif event.type == "tool_result":
            return "tool.result"
        elif event.type == "user":
            return "user.message"
        elif event.type == "assistant":
            return "assistant.response"
        else:
            return f"event.{event.type}"

    def record_metrics(self, event: ClaudeEvent):
        """
        Record metrics for a Claude event.

        Args:
            event: The Claude event
        """
        # Common attributes
        attributes = {
            "session.id": event.session_id,
            "message.type": event.type,
        }

        if event.model:
            attributes["model"] = event.model

        # Token metrics
        if event.tokens_input > 0:
            self.tokens_input_counter.add(event.tokens_input, attributes)

        if event.tokens_output > 0:
            self.tokens_output_counter.add(event.tokens_output, attributes)

        if event.tokens_cache_creation > 0:
            self.tokens_cache_creation_counter.add(
                event.tokens_cache_creation, attributes
            )

        if event.tokens_cache_read > 0:
            self.tokens_cache_read_counter.add(event.tokens_cache_read, attributes)

        if event.total_tokens > 0:
            self.tokens_total_counter.add(event.total_tokens, attributes)

        # Cost
        if event.cost_usd > 0:
            self.cost_counter.add(event.cost_usd, attributes)

        # Message count
        if event.is_message_event():
            self.message_counter.add(1, attributes)

        # Tool usage
        if event.type == "tool_use" and event.tool_name:
            tool_attributes = {**attributes, "tool.name": event.tool_name}
            self.tool_usage_counter.add(1, tool_attributes)
