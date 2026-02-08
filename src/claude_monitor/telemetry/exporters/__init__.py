"""
Telemetry Exporters Package.

This package provides pluggable exporter backends for sending
OpenTelemetry telemetry to various observability platforms.

Supported Exporters:
- Splunk: Enterprise SIEM and observability platform
- Dynatrace: APM and infrastructure monitoring (stub)
- Langfuse: LLM-specific observability platform (stub)

Architecture:
- BaseExporter: Abstract base class for all exporters
- ExporterRegistry: Registry for discovering available exporters
- ExporterFactory: Factory for creating and managing exporters

Adding a New Exporter:
1. Create a new file (e.g., datadog.py)
2. Subclass BaseExporter
3. Implement required methods (configure, validate_config, etc.)
4. Register in this __init__.py

Example:
    from claude_monitor.telemetry.exporters import get_global_registry
    from claude_monitor.telemetry.exporters.splunk import SplunkExporter

    registry = get_global_registry()
    exporter = registry.create_exporter("splunk", config)
"""

from claude_monitor.telemetry.exporters.base import BaseExporter
from claude_monitor.telemetry.exporters.base import ExporterFactory
from claude_monitor.telemetry.exporters.base import ExporterRegistry
from claude_monitor.telemetry.exporters.base import get_global_registry
from claude_monitor.telemetry.exporters.base import register_exporter


# Import and register all available exporters
try:
    from claude_monitor.telemetry.exporters.splunk import SplunkExporter

    register_exporter(SplunkExporter)
except ImportError as e:
    import logging

    logging.warning(f"Splunk exporter not available: {e}")

try:
    from claude_monitor.telemetry.exporters.dynatrace import (
        DynatraceExporter,
    )

    register_exporter(DynatraceExporter)
except ImportError as e:
    import logging

    logging.warning(f"Dynatrace exporter not available: {e}")

try:
    from claude_monitor.telemetry.exporters.langfuse import LangfuseExporter

    register_exporter(LangfuseExporter)
except ImportError as e:
    import logging

    logging.warning(f"Langfuse exporter not available: {e}")


__all__ = [
    # Base classes
    "BaseExporter",
    "ExporterRegistry",
    "ExporterFactory",
    # Registry functions
    "get_global_registry",
    "register_exporter",
    # Concrete exporters (if imported successfully)
    "SplunkExporter",
    "DynatraceExporter",
    "LangfuseExporter",
]
