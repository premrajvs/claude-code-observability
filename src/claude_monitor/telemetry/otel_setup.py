"""
OpenTelemetry SDK initialization and configuration.
"""

import logging
from typing import Optional

from opentelemetry import metrics
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from claude_monitor.telemetry.models import TelemetryConfig


logger = logging.getLogger(__name__)

# Global references to providers
_tracer_provider: Optional[TracerProvider] = None
_meter_provider: Optional[MeterProvider] = None


def create_resource(config: TelemetryConfig) -> Resource:
    """
    Create OpenTelemetry resource with service identification.

    Resource attributes identify the source of telemetry and provide
    context for all signals (traces, metrics, logs).
    """
    import platform

    return Resource.create(
        {
            "service.name": config.service_name,
            "service.version": config.service_version,
            "deployment.environment": config.deployment_environment,
            "telemetry.sdk.name": "opentelemetry",
            "telemetry.sdk.language": "python",
            "host.name": platform.node(),
            "os.type": platform.system(),
            "process.pid": str(platform.os.getpid()),
        }
    )


def initialize_telemetry(
    config: Optional[TelemetryConfig] = None,
) -> tuple[trace.Tracer, metrics.Meter]:
    """
    Initialize OpenTelemetry SDK with configured exporters.

    Args:
        config: Telemetry configuration. If None, loads from environment.

    Returns:
        Tuple of (tracer, meter) for creating spans and metrics.
    """
    global _tracer_provider, _meter_provider

    if config is None:
        config = TelemetryConfig.from_env()

    logger.info(f"Initializing telemetry with config: {config}")

    # Create resource
    resource = create_resource(config)

    # Initialize tracing
    _tracer_provider = _initialize_tracing(config, resource)

    # Initialize metrics
    _meter_provider = _initialize_metrics(config, resource)

    # Get tracer and meter
    tracer = trace.get_tracer(__name__)
    meter = metrics.get_meter(__name__)

    logger.info("Telemetry initialization complete")
    return tracer, meter


def _initialize_tracing(config: TelemetryConfig, resource: Resource) -> TracerProvider:
    """Initialize trace provider with OTLP exporter."""
    tracer_provider = TracerProvider(resource=resource)

    # Configure OTLP exporter
    if config.use_collector:
        otlp_exporter = OTLPSpanExporter(
            endpoint=f"{config.collector_endpoint}/v1/traces",
        )
        span_processor = BatchSpanProcessor(otlp_exporter)
        tracer_provider.add_span_processor(span_processor)
        logger.info(f"Configured OTLP trace exporter to {config.collector_endpoint}")
    else:
        # TODO: Add direct Splunk HEC exporter
        logger.warning("Direct mode not yet implemented, using console exporter")
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter

        console_exporter = ConsoleSpanExporter()
        span_processor = BatchSpanProcessor(console_exporter)
        tracer_provider.add_span_processor(span_processor)

    # Set as global tracer provider
    trace.set_tracer_provider(tracer_provider)

    return tracer_provider


def _initialize_metrics(config: TelemetryConfig, resource: Resource) -> MeterProvider:
    """Initialize meter provider with OTLP exporter."""
    # Configure OTLP exporter
    if config.use_collector:
        otlp_exporter = OTLPMetricExporter(
            endpoint=f"{config.collector_endpoint}/v1/metrics",
        )
        metric_reader = PeriodicExportingMetricReader(
            otlp_exporter,
            export_interval_millis=config.batch_timeout_seconds * 1000,
        )
        logger.info(f"Configured OTLP metric exporter to {config.collector_endpoint}")
    else:
        # TODO: Add direct Splunk HEC exporter
        logger.warning("Direct mode not yet implemented, using console exporter")
        from opentelemetry.sdk.metrics.export import ConsoleMetricExporter

        console_exporter = ConsoleMetricExporter()
        metric_reader = PeriodicExportingMetricReader(
            console_exporter,
            export_interval_millis=config.batch_timeout_seconds * 1000,
        )

    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[metric_reader],
    )

    # Set as global meter provider
    metrics.set_meter_provider(meter_provider)

    return meter_provider


def shutdown_telemetry():
    """
    Gracefully shutdown telemetry providers.

    Ensures all pending telemetry is exported before shutdown.
    """
    global _tracer_provider, _meter_provider

    logger.info("Shutting down telemetry")

    if _tracer_provider:
        _tracer_provider.shutdown()
        _tracer_provider = None

    if _meter_provider:
        _meter_provider.shutdown()
        _meter_provider = None

    logger.info("Telemetry shutdown complete")


def get_tracer() -> trace.Tracer:
    """Get the global tracer instance."""
    return trace.get_tracer(__name__)


def get_meter() -> metrics.Meter:
    """Get the global meter instance."""
    return metrics.get_meter(__name__)
