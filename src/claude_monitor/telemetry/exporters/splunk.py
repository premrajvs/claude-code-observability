"""
Splunk HEC (HTTP Event Collector) Exporter.

This exporter sends OpenTelemetry traces and metrics to Splunk Enterprise
or Splunk Cloud via the HTTP Event Collector.

Configuration:
    - endpoint: Splunk HEC endpoint URL
    - token: HEC authentication token
    - index: Splunk index name
    - source: Event source name
    - sourcetype: Event source type
    - verify_ssl: Whether to verify SSL certificates

Example:
    config = {
        "endpoint": "http://localhost:8088/services/collector",
        "token": "your-hec-token",
        "index": "idx-claudecode",
        "source": "claude:observatory",
        "sourcetype": "otel:traces"
    }

    exporter = SplunkExporter()
    exporter.configure(config)
"""

import logging
from typing import Any
from typing import Dict

import requests
from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
    OTLPMetricExporter,
)
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from claude_monitor.telemetry.exporters.base import BaseExporter


logger = logging.getLogger(__name__)


class SplunkExporter(BaseExporter):
    """
    Splunk HEC exporter for OpenTelemetry telemetry.

    Sends traces and metrics to Splunk via OTLP → OTel Collector → HEC pipeline.
    """

    name = "splunk"

    def __init__(self, enabled: bool = True):
        """Initialize Splunk exporter."""
        super().__init__(enabled)
        self._hec_endpoint: str = ""
        self._hec_token: str = ""
        self._index: str = "main"
        self._source: str = "otel"
        self._sourcetype: str = "_json"
        self._verify_ssl: bool = True
        self._otlp_endpoint: str = "http://localhost:4318"

    def _initialize(self) -> None:
        """Initialize Splunk-specific components."""
        # Extract configuration
        self._hec_endpoint = self._config.get(
            "hec_endpoint", "http://localhost:8088/services/collector"
        )
        self._hec_token = self._config.get("hec_token", "")
        self._index = self._config.get("index", "main")
        self._source = self._config.get("source", "otel")
        self._sourcetype = self._config.get("sourcetype", "_json")
        self._verify_ssl = self._config.get("verify_ssl", True)
        self._otlp_endpoint = self._config.get(
            "otlp_endpoint", "http://localhost:4318"
        )

        # Create OTLP exporters (for Collector)
        # The Collector will forward to Splunk HEC
        span_exporter = OTLPSpanExporter(
            endpoint=f"{self._otlp_endpoint}/v1/traces",
        )

        metric_exporter = OTLPMetricExporter(
            endpoint=f"{self._otlp_endpoint}/v1/metrics",
        )

        # Create processors/readers
        self._span_processor = BatchSpanProcessor(span_exporter)
        self._metric_reader = PeriodicExportingMetricReader(
            metric_exporter,
            export_interval_millis=10000,  # 10 seconds
        )

        logger.info(
            f"Splunk exporter initialized: OTLP={self._otlp_endpoint}, "
            f"HEC={self._hec_endpoint}, index={self._index}"
        )

    def validate_config(self) -> bool:
        """
        Validate Splunk configuration.

        Returns:
            True if valid

        Raises:
            ValueError: If configuration is invalid
        """
        errors = []

        # Check OTLP endpoint
        otlp_endpoint = self._config.get("otlp_endpoint")
        if not otlp_endpoint:
            errors.append("Missing 'otlp_endpoint'")

        # Check HEC configuration (optional if using Collector)
        # If HEC endpoint is provided, validate token
        hec_endpoint = self._config.get("hec_endpoint")
        if hec_endpoint:
            hec_token = self._config.get("hec_token")
            if not hec_token:
                errors.append(
                    "HEC endpoint provided but missing 'hec_token'"
                )

        if errors:
            raise ValueError(f"Splunk config invalid: {', '.join(errors)}")

        return True

    def _health_check_impl(self) -> bool:
        """Check if Splunk HEC is reachable."""
        try:
            # Check HEC health endpoint
            health_url = f"{self._hec_endpoint}/health"
            response = requests.get(
                health_url, verify=self._verify_ssl, timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Splunk health check failed: {e}")
            return False

    def get_span_processor(self):
        """Get the span processor."""
        if self._span_processor is None:
            raise RuntimeError(
                f"{self.name} exporter not initialized. Call configure() first."
            )
        return self._span_processor

    def get_metric_reader(self):
        """Get the metric reader."""
        if self._metric_reader is None:
            raise RuntimeError(
                f"{self.name} exporter not initialized. Call configure() first."
            )
        return self._metric_reader
