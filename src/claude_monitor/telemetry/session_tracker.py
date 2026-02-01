"""
Track Claude Code sessions and manage span lifecycle.
"""

import logging
from datetime import datetime
from typing import Dict
from typing import Optional

from opentelemetry import trace

from claude_monitor.telemetry.models import ClaudeEvent
from claude_monitor.telemetry.models import SessionMetadata


logger = logging.getLogger(__name__)


class SessionTracker:
    """
    Manages active sessions and their OpenTelemetry spans.

    Each session gets a root span, with child spans for individual messages
    and tool interactions.
    """

    def __init__(self, tracer: trace.Tracer):
        self.tracer = tracer

        # Active sessions: session_id -> SessionMetadata
        self._sessions: Dict[str, SessionMetadata] = {}

        # Active root spans: session_id -> Span
        self._root_spans: Dict[str, trace.Span] = {}

        # Active message spans: message_id -> Span
        self._message_spans: Dict[str, trace.Span] = {}

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
        if session_id in self._sessions:
            logger.warning(f"Session {session_id} already exists")
            return self._root_spans[session_id]

        # Create session metadata
        metadata = SessionMetadata(
            session_id=session_id,
            project_path=project_path,
            session_slug=session_slug,
            start_time=datetime.now(),
            model=model,
        )
        self._sessions[session_id] = metadata

        # Create root span
        span = self.tracer.start_span(
            f"session.{session_slug or session_id[:8]}",
            start_time=int(metadata.start_time.timestamp() * 1e9),
        )

        # Set session attributes
        span.set_attribute("session.id", session_id)
        span.set_attribute("session.project_path", project_path)
        span.set_attribute("session.slug", session_slug)

        if model:
            span.set_attribute("model", model)

        self._root_spans[session_id] = span

        logger.info(f"Started session {session_id}")
        return span

    def end_session(self, session_id: str):
        """
        End a session and close its root span.

        Args:
            session_id: Session identifier
        """
        if session_id not in self._sessions:
            logger.warning(f"Session {session_id} not found")
            return

        metadata = self._sessions[session_id]
        metadata.end_time = datetime.now()

        # Get root span
        root_span = self._root_spans.get(session_id)
        if root_span:
            # Set final attributes
            root_span.set_attribute("session.total_messages", metadata.total_messages)
            root_span.set_attribute("session.total_tokens", metadata.total_tokens)
            root_span.set_attribute("session.total_cost", metadata.total_cost)

            if metadata.duration_seconds:
                root_span.set_attribute(
                    "session.duration_seconds", metadata.duration_seconds
                )

            # End span
            root_span.end(end_time=int(metadata.end_time.timestamp() * 1e9))
            del self._root_spans[session_id]

        logger.info(
            f"Ended session {session_id} "
            f"(duration: {metadata.duration_seconds:.2f}s, "
            f"messages: {metadata.total_messages}, "
            f"cost: ${metadata.total_cost:.4f})"
        )

    def process_event(self, event: ClaudeEvent, span: trace.Span):
        """
        Process an event and update session metadata.

        Args:
            event: The Claude event
            span: The span created for this event
        """
        session_id = event.session_id

        # Ensure session exists
        if session_id not in self._sessions:
            self.start_session(
                session_id,
                project_path=event.project_path or "",
                session_slug=event.session_slug or "",
                model=event.model,
            )

        metadata = self._sessions[session_id]

        # Update aggregated metrics
        if event.is_message_event():
            metadata.total_messages += 1

        metadata.total_tokens += event.total_tokens
        metadata.total_cost += event.cost_usd

        if event.tool_name:
            metadata.tools_used[event.tool_name] = (
                metadata.tools_used.get(event.tool_name, 0) + 1
            )

        # Track message span for potential parent-child relationships
        if event.message_id:
            self._message_spans[event.message_id] = span

    def get_session_span(self, session_id: str) -> Optional[trace.Span]:
        """
        Get the root span for a session.

        Args:
            session_id: Session identifier

        Returns:
            Root span or None if session not found
        """
        return self._root_spans.get(session_id)

    def get_message_span(self, message_id: str) -> Optional[trace.Span]:
        """
        Get the span for a specific message.

        Args:
            message_id: Message identifier

        Returns:
            Message span or None if not found
        """
        return self._message_spans.get(message_id)

    def get_session_metadata(self, session_id: str) -> Optional[SessionMetadata]:
        """
        Get metadata for a session.

        Args:
            session_id: Session identifier

        Returns:
            SessionMetadata or None if session not found
        """
        return self._sessions.get(session_id)

    def flush_completed_sessions(self, max_age_hours: int = 24):
        """
        Clean up old completed sessions from memory.

        Args:
            max_age_hours: Maximum age of completed sessions to keep
        """
        now = datetime.now()
        to_remove = []

        for session_id, metadata in self._sessions.items():
            if metadata.end_time:
                age_hours = (now - metadata.end_time).total_seconds() / 3600
                if age_hours > max_age_hours:
                    to_remove.append(session_id)

        for session_id in to_remove:
            del self._sessions[session_id]
            # Clean up any lingering spans
            self._message_spans = {
                k: v
                for k, v in self._message_spans.items()
                if not k.startswith(session_id)
            }

        if to_remove:
            logger.info(f"Flushed {len(to_remove)} completed sessions")

    def get_active_session_count(self) -> int:
        """Get count of active sessions."""
        return sum(1 for s in self._sessions.values() if s.is_active)

    def get_all_sessions(self) -> Dict[str, SessionMetadata]:
        """Get all tracked sessions."""
        return self._sessions.copy()
