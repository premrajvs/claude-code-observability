"""
Watch Claude Code log files for new events.
"""

import logging
import os
import time
from pathlib import Path
from typing import Callable
from typing import Dict
from typing import Optional
from typing import Set

from watchdog.events import FileSystemEvent
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from claude_monitor.telemetry.event_transformer import OTelTransformer
from claude_monitor.telemetry.models import ClaudeEvent
from claude_monitor.telemetry.session_tracker import SessionTracker


logger = logging.getLogger(__name__)


class ClaudeLogHandler(FileSystemEventHandler):
    """
    Handle file system events for Claude Code log files.
    """

    def __init__(
        self,
        transformer: OTelTransformer,
        session_tracker: SessionTracker,
        event_callback: Optional[Callable[[ClaudeEvent], None]] = None,
    ):
        self.transformer = transformer
        self.session_tracker = session_tracker
        self.event_callback = event_callback

        # Track file positions to avoid re-processing
        self._file_positions: Dict[str, int] = {}

        # Track which sessions we've seen
        self._known_sessions: Set[str] = set()

    def on_modified(self, event: FileSystemEvent):
        """Handle file modification events."""
        if event.is_directory:
            return

        file_path = event.src_path
        if not file_path.endswith(".jsonl"):
            return

        self._process_file(file_path)

    def on_created(self, event: FileSystemEvent):
        """Handle file creation events."""
        if event.is_directory:
            return

        file_path = event.src_path
        if not file_path.endswith(".jsonl"):
            return

        logger.info(f"New log file created: {file_path}")
        self._process_file(file_path)

    def _process_file(self, file_path: str):
        """
        Process a JSONL log file incrementally.

        Args:
            file_path: Path to the JSONL file
        """
        try:
            # Extract session ID from filename
            session_id = self._extract_session_id(file_path)
            if not session_id:
                logger.warning(f"Could not extract session ID from {file_path}")
                return

            # Get current file position
            last_position = self._file_positions.get(file_path, 0)

            # Read new lines
            with open(file_path, "r", encoding="utf-8") as f:
                # Seek to last position
                f.seek(last_position)

                # Read new lines
                new_lines = f.readlines()
                new_position = f.tell()

                # Update position
                self._file_positions[file_path] = new_position

            # Process new lines
            for line in new_lines:
                if line.strip():
                    self._process_line(line, session_id)

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}", exc_info=True)

    def _process_line(self, line: str, session_id: str):
        """
        Process a single JSONL line.

        Args:
            line: JSONL line
            session_id: Session ID
        """
        try:
            # Parse event
            event = self.transformer.parse_jsonl_line(line, session_id)
            if not event:
                return

            # Start session if new
            if session_id not in self._known_sessions:
                self.session_tracker.start_session(
                    session_id,
                    project_path=event.project_path or "",
                    session_slug=event.session_slug or "",
                    model=event.model,
                )
                self._known_sessions.add(session_id)

            # Get session context for span parent
            session_span = self.session_tracker.get_session_span(session_id)
            parent_context = (
                trace.set_span_in_context(session_span) if session_span else None
            )

            # Create span
            span = self.transformer.create_span(event, parent_context)

            # Record metrics
            self.transformer.record_metrics(event)

            # Update session tracking
            self.session_tracker.process_event(event, span)

            # End span
            span.end()

            # Call event callback if provided
            if self.event_callback:
                self.event_callback(event)

        except Exception as e:
            logger.error(f"Error processing line: {e}", exc_info=True)

    def _extract_session_id(self, file_path: str) -> Optional[str]:
        """
        Extract session ID from JSONL filename.

        Claude Code logs are named: {session_id}.jsonl

        Args:
            file_path: Path to JSONL file

        Returns:
            Session ID or None
        """
        try:
            filename = Path(file_path).stem  # Get filename without extension
            return filename
        except Exception as e:
            logger.error(f"Error extracting session ID: {e}")
            return None


class ClaudeLogWatcher:
    """
    Watch Claude Code logs directory for new sessions and events.
    """

    def __init__(
        self,
        transformer: OTelTransformer,
        session_tracker: SessionTracker,
        watch_directory: Optional[str] = None,
        event_callback: Optional[Callable[[ClaudeEvent], None]] = None,
    ):
        self.transformer = transformer
        self.session_tracker = session_tracker
        self.event_callback = event_callback

        # Determine watch directory
        if watch_directory:
            self.watch_directory = Path(watch_directory)
        else:
            # Default to ~/.claude/projects
            home = Path.home()
            self.watch_directory = home / ".claude" / "projects"

        if not self.watch_directory.exists():
            raise ValueError(
                f"Watch directory does not exist: {self.watch_directory}"
            )

        # Create event handler
        self.handler = ClaudeLogHandler(
            transformer=transformer,
            session_tracker=session_tracker,
            event_callback=event_callback,
        )

        # Create observer
        self.observer = Observer()
        self.observer.schedule(
            self.handler, str(self.watch_directory), recursive=True
        )

        self._running = False

    def start(self):
        """Start watching for file changes."""
        logger.info(f"Starting file watcher on {self.watch_directory}")

        # Process existing files first
        self._process_existing_files()

        # Start observer
        self.observer.start()
        self._running = True

        logger.info("File watcher started")

    def stop(self):
        """Stop watching for file changes."""
        logger.info("Stopping file watcher")
        self._running = False
        self.observer.stop()
        self.observer.join()
        logger.info("File watcher stopped")

    def is_running(self) -> bool:
        """Check if watcher is running."""
        return self._running

    def run(self):
        """
        Run the watcher in the foreground.

        This will block until stopped.
        """
        self.start()
        try:
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        finally:
            self.stop()

    def _process_existing_files(self):
        """Process existing JSONL files in the watch directory."""
        logger.info("Processing existing log files")

        count = 0
        for root, _, files in os.walk(self.watch_directory):
            for file in files:
                if file.endswith(".jsonl"):
                    file_path = os.path.join(root, file)
                    self.handler._process_file(file_path)
                    count += 1

        logger.info(f"Processed {count} existing log files")


# Import trace here to avoid circular import
from opentelemetry import trace
