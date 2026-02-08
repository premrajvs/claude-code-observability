"""
Example: Using the OpenTelemetry telemetry system programmatically.
"""

import time

from claude_monitor.telemetry import ClaudeLogWatcher
from claude_monitor.telemetry import initialize_telemetry
from claude_monitor.telemetry import shutdown_telemetry
from claude_monitor.telemetry.event_transformer import OTelTransformer
from claude_monitor.telemetry.models import ClaudeEvent
from claude_monitor.telemetry.models import TelemetryConfig
from claude_monitor.telemetry.session_tracker import SessionTracker


def event_callback(event: ClaudeEvent):
    """
    Custom callback for processing events.

    This function is called for each event processed from the JSONL logs.
    """
    print(f"\n[Event] {event.type}")
    print(f"  Session: {event.session_id}")
    print(f"  Message: {event.message_id}")

    if event.tokens_input > 0:
        print(f"  Input Tokens: {event.tokens_input:,}")

    if event.tokens_output > 0:
        print(f"  Output Tokens: {event.tokens_output:,}")

    if event.cost_usd > 0:
        print(f"  Cost: ${event.cost_usd:.4f}")

    if event.tool_name:
        print(f"  Tool: {event.tool_name}")

    # Custom alerting logic
    if event.cost_usd > 0.50:
        print(f"  ⚠️ HIGH COST EVENT: ${event.cost_usd:.4f}")


def main():
    """
    Example: Start telemetry collection with custom event processing.
    """
    print("=" * 60)
    print("Claude Monitor - OpenTelemetry Example")
    print("=" * 60)

    # Create configuration
    config = TelemetryConfig(
        service_name="claude-monitor-example",
        use_collector=True,
        collector_endpoint="http://localhost:4318",
        deployment_environment="development",
    )

    print(f"\nConfiguration:")
    print(f"  Service Name: {config.service_name}")
    print(f"  Mode: {'Collector' if config.use_collector else 'Direct'}")
    print(f"  Collector Endpoint: {config.collector_endpoint}")
    print(f"  Watch Directory: {config.watch_directory or '~/.claude/projects'}")

    # Initialize OpenTelemetry
    print("\nInitializing OpenTelemetry...")
    tracer, meter = initialize_telemetry(config)
    print("✓ OpenTelemetry initialized")

    # Create transformer and session tracker
    transformer = OTelTransformer(tracer, meter)
    session_tracker = SessionTracker(tracer)

    # Create file watcher with custom callback
    print("\nStarting file watcher...")
    watcher = ClaudeLogWatcher(
        transformer=transformer,
        session_tracker=session_tracker,
        watch_directory=config.watch_directory,
        event_callback=event_callback,  # Custom callback
    )

    watcher.start()
    print("✓ File watcher started")

    print("\n" + "=" * 60)
    print("Monitoring Claude Code logs...")
    print("Press Ctrl+C to stop")
    print("=" * 60)

    try:
        # Run indefinitely
        while watcher.is_running():
            time.sleep(1)

            # Periodically print session statistics
            if int(time.time()) % 60 == 0:  # Every minute
                active_sessions = session_tracker.get_active_session_count()
                print(f"\n[Stats] Active Sessions: {active_sessions}")

                # Print details for each session
                for session_id, metadata in session_tracker.get_all_sessions().items():
                    if metadata.is_active:
                        print(f"  {session_id[:12]}...")
                        print(f"    Messages: {metadata.total_messages}")
                        print(f"    Tokens: {metadata.total_tokens:,}")
                        print(f"    Cost: ${metadata.total_cost:.4f}")

            # Flush old sessions every hour
            if int(time.time()) % 3600 == 0:
                session_tracker.flush_completed_sessions(max_age_hours=24)

    except KeyboardInterrupt:
        print("\n\nStopping telemetry collection...")

    # Cleanup
    watcher.stop()
    print("✓ File watcher stopped")

    shutdown_telemetry()
    print("✓ OpenTelemetry shutdown")

    print("\nTelemetry collection stopped successfully!")


if __name__ == "__main__":
    main()
