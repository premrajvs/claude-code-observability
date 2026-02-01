"""
CLI commands for OpenTelemetry telemetry collection.
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Optional

from rich.console import Console

from claude_monitor.telemetry import ClaudeLogWatcher
from claude_monitor.telemetry import initialize_telemetry
from claude_monitor.telemetry import shutdown_telemetry
from claude_monitor.telemetry.event_transformer import OTelTransformer
from claude_monitor.telemetry.models import TelemetryConfig
from claude_monitor.telemetry.session_tracker import SessionTracker


logger = logging.getLogger(__name__)
console = Console()


def setup_telemetry_parser(subparsers) -> argparse.ArgumentParser:
    """
    Add telemetry subcommand to CLI parser.

    Args:
        subparsers: Subparsers from main argument parser

    Returns:
        Telemetry subcommand parser
    """
    parser = subparsers.add_parser(
        "telemetry",
        help="OpenTelemetry-based telemetry collection",
        description="Monitor Claude Code sessions and export telemetry to observability backends",
    )

    # Mode selection
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--enable",
        action="store_true",
        help="Start telemetry collection",
    )
    mode_group.add_argument(
        "--disable",
        action="store_true",
        help="Stop telemetry collection (not yet implemented)",
    )
    mode_group.add_argument(
        "--test",
        action="store_true",
        help="Test telemetry connection and send sample data",
    )

    # Configuration options
    parser.add_argument(
        "--collector-mode",
        action="store_true",
        default=True,
        help="Use OpenTelemetry Collector (default)",
    )
    parser.add_argument(
        "--direct-mode",
        action="store_true",
        help="Send directly to Splunk HEC (not recommended)",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run in background daemon mode",
    )

    # Watch directory
    parser.add_argument(
        "--watch-dir",
        type=str,
        help="Directory to watch for Claude logs (default: ~/.claude/projects)",
    )

    # Collector endpoint
    parser.add_argument(
        "--collector-endpoint",
        type=str,
        default="http://localhost:4318",
        help="OpenTelemetry Collector OTLP HTTP endpoint",
    )

    # Splunk HEC (for direct mode)
    parser.add_argument(
        "--splunk-token",
        type=str,
        help="Splunk HEC token (for direct mode)",
    )
    parser.add_argument(
        "--splunk-url",
        type=str,
        help="Splunk HEC URL (for direct mode)",
    )

    parser.set_defaults(func=handle_telemetry_command)

    return parser


def handle_telemetry_command(args: argparse.Namespace) -> int:
    """
    Handle telemetry command execution.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    if args.enable:
        return run_telemetry(args)
    elif args.test:
        return test_telemetry(args)
    elif args.disable:
        console.print("[yellow]Disable command not yet implemented[/yellow]")
        return 1

    return 0


def run_telemetry(args: argparse.Namespace) -> int:
    """
    Start telemetry collection.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code
    """
    console.print("[bold green]Starting Claude Monitor Telemetry[/bold green]")

    try:
        # Create configuration
        config = create_config_from_args(args)

        # Validate watch directory
        watch_dir = Path(config.watch_directory) if config.watch_directory else None
        if watch_dir and not watch_dir.exists():
            console.print(
                f"[bold red]Error:[/bold red] Watch directory does not exist: {watch_dir}"
            )
            return 1

        # Initialize OpenTelemetry
        console.print(
            f"[cyan]Initializing OpenTelemetry (mode: {'collector' if config.use_collector else 'direct'})[/cyan]"
        )
        tracer, meter = initialize_telemetry(config)

        # Create transformer and session tracker
        transformer = OTelTransformer(tracer, meter)
        session_tracker = SessionTracker(tracer)

        # Create file watcher
        console.print(f"[cyan]Watching directory: {config.watch_directory}[/cyan]")
        watcher = ClaudeLogWatcher(
            transformer=transformer,
            session_tracker=session_tracker,
            watch_directory=config.watch_directory,
        )

        # Start watching
        watcher.start()

        console.print("[bold green]Telemetry collection started successfully![/bold green]")
        console.print("\n[yellow]Press Ctrl+C to stop[/yellow]\n")

        # Run in foreground
        try:
            while watcher.is_running():
                time.sleep(1)

                # Periodically flush old sessions
                if int(time.time()) % 3600 == 0:  # Every hour
                    session_tracker.flush_completed_sessions()

        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping telemetry collection...[/yellow]")

        # Stop watcher
        watcher.stop()

        # Shutdown telemetry
        shutdown_telemetry()

        console.print("[bold green]Telemetry collection stopped[/bold green]")
        return 0

    except Exception as e:
        logger.error(f"Error running telemetry: {e}", exc_info=True)
        console.print(f"[bold red]Error:[/bold red] {e}")
        return 1


def test_telemetry(args: argparse.Namespace) -> int:
    """
    Test telemetry connection and send sample data.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code
    """
    console.print("[bold cyan]Testing Telemetry Connection[/bold cyan]\n")

    try:
        # Create configuration
        config = create_config_from_args(args)

        # Initialize OpenTelemetry
        console.print("[cyan]Initializing OpenTelemetry...[/cyan]")
        tracer, meter = initialize_telemetry(config)

        # Create test span
        console.print("[cyan]Creating test trace...[/cyan]")
        with tracer.start_as_current_span("test.session") as span:
            span.set_attribute("test", "true")
            span.set_attribute("session.id", "test-session-123")
            span.set_attribute("tokens.total", 100)
            span.set_attribute("cost.usd", 0.01)

            # Create child span
            with tracer.start_as_current_span("test.message") as child_span:
                child_span.set_attribute("message.type", "user")
                child_span.set_attribute("content", "Test message")

        # Create test metrics
        console.print("[cyan]Recording test metrics...[/cyan]")
        test_counter = meter.create_counter(
            "claude.test.counter",
            description="Test counter metric",
        )
        test_counter.add(1, {"test": "true"})

        console.print("[cyan]Flushing telemetry...[/cyan]")

        # Give time for export
        time.sleep(2)

        # Shutdown
        shutdown_telemetry()

        console.print("\n[bold green]Test completed successfully![/bold green]")
        console.print(
            "\n[yellow]Check your collector logs and backend to verify data arrival[/yellow]"
        )

        return 0

    except Exception as e:
        logger.error(f"Error testing telemetry: {e}", exc_info=True)
        console.print(f"\n[bold red]Test failed:[/bold red] {e}")
        return 1


def create_config_from_args(args: argparse.Namespace) -> TelemetryConfig:
    """
    Create telemetry configuration from command line arguments.

    Args:
        args: Parsed command line arguments

    Returns:
        TelemetryConfig instance
    """
    # Start with environment-based config
    config = TelemetryConfig.from_env()

    # Override with command line arguments
    if hasattr(args, "direct_mode") and args.direct_mode:
        config.use_collector = False

    if hasattr(args, "collector_endpoint") and args.collector_endpoint:
        config.collector_endpoint = args.collector_endpoint

    if hasattr(args, "watch_dir") and args.watch_dir:
        config.watch_directory = args.watch_dir

    if hasattr(args, "splunk_token") and args.splunk_token:
        config.splunk_hec_token = args.splunk_token

    if hasattr(args, "splunk_url") and args.splunk_url:
        config.splunk_hec_url = args.splunk_url

    # Set default watch directory if not specified
    if not config.watch_directory:
        home = Path.home()
        config.watch_directory = str(home / ".claude" / "projects")

    return config


def main(argv: Optional[list] = None) -> int:
    """
    Standalone entry point for telemetry command.

    Args:
        argv: Command line arguments (default: sys.argv[1:])

    Returns:
        Exit code
    """
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="Claude Monitor OpenTelemetry Telemetry"
    )
    subparsers = parser.add_subparsers(dest="command")

    setup_telemetry_parser(subparsers)

    args = parser.parse_args(argv)

    if hasattr(args, "func"):
        return args.func(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
