"""
Base classes and abstractions for telemetry exporters.

This module provides the foundation for pluggable exporter backends,
enabling easy integration with Splunk, Dynatrace, Langfuse, Datadog, etc.

Architecture:
- BaseExporter: Abstract base class with common functionality
- ExporterFactory: Factory for creating and managing exporters
- ExporterRegistry: Registry for discovering available exporters
"""

import logging
from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Type

from opentelemetry import metrics
from opentelemetry import trace
from opentelemetry.sdk.metrics.export import MetricReader
from opentelemetry.sdk.trace.export import SpanProcessor

from claude_monitor.telemetry.interfaces import TelemetryExporter


logger = logging.getLogger(__name__)


class BaseExporter(TelemetryExporter, ABC):
    """
    Abstract base class for telemetry exporters.

    Provides common functionality and enforces interface contract.
    Subclasses implement backend-specific logic.

    Example:
        class SplunkExporter(BaseExporter):
            name = "splunk"

            def configure(self, config):
                self.hec_token = config["token"]
                self.hec_url = config["url"]
                ...
    """

    def __init__(self, enabled: bool = True):
        """
        Initialize the exporter.

        Args:
            enabled: Whether this exporter is enabled
        """
        self._enabled = enabled
        self._config: Dict[str, Any] = {}
        self._span_processor: Optional[SpanProcessor] = None
        self._metric_reader: Optional[MetricReader] = None
        self._initialized = False

    @property
    @abstractmethod
    def name(self) -> str:
        """Exporter name (must be unique)."""
        ...

    @property
    def enabled(self) -> bool:
        """Whether this exporter is enabled."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Set enabled state."""
        self._enabled = value

    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the exporter.

        Args:
            config: Configuration dictionary

        Raises:
            ValueError: If configuration is invalid
        """
        self._config = config

        # Validate configuration
        if not self.validate_config():
            raise ValueError(f"Invalid configuration for {self.name} exporter")

        # Initialize exporter components
        try:
            self._initialize()
            self._initialized = True
            logger.info(f"{self.name} exporter configured successfully")
        except Exception as e:
            logger.error(
                f"Failed to initialize {self.name} exporter: {e}",
                exc_info=True,
            )
            raise

    @abstractmethod
    def _initialize(self) -> None:
        """
        Initialize exporter-specific components.

        Called after configuration is validated.
        Subclasses implement backend-specific initialization.
        """
        ...

    @abstractmethod
    def get_span_processor(self) -> SpanProcessor:
        """Get the span processor for this exporter."""
        ...

    @abstractmethod
    def get_metric_reader(self) -> MetricReader:
        """Get the metric reader for this exporter."""
        ...

    @abstractmethod
    def validate_config(self) -> bool:
        """
        Validate exporter configuration.

        Returns:
            True if valid

        Raises:
            ValueError: If invalid with detailed message
        """
        ...

    def health_check(self) -> bool:
        """
        Check if exporter backend is reachable.

        Returns:
            True if healthy, False otherwise
        """
        if not self._initialized:
            logger.warning(f"{self.name} exporter not initialized")
            return False

        try:
            return self._health_check_impl()
        except Exception as e:
            logger.error(
                f"Health check failed for {self.name}: {e}", exc_info=True
            )
            return False

    @abstractmethod
    def _health_check_impl(self) -> bool:
        """Backend-specific health check implementation."""
        ...

    def shutdown(self) -> None:
        """Gracefully shutdown the exporter."""
        try:
            if self._span_processor:
                self._span_processor.shutdown()
            if self._metric_reader:
                self._metric_reader.shutdown()
            logger.info(f"{self.name} exporter shutdown complete")
        except Exception as e:
            logger.error(
                f"Error during {self.name} shutdown: {e}", exc_info=True
            )

    def __repr__(self) -> str:
        """String representation."""
        status = "enabled" if self._enabled else "disabled"
        init = "initialized" if self._initialized else "not initialized"
        return f"<{self.__class__.__name__}(name={self.name}, {status}, {init})>"


class ExporterRegistry:
    """
    Registry for discovering and managing available exporters.

    Enables plugin-style architecture where exporters can be:
    - Auto-discovered
    - Registered dynamically
    - Listed for configuration
    """

    def __init__(self):
        """Initialize the registry."""
        self._exporters: Dict[str, Type[BaseExporter]] = {}

    def register(
        self, exporter_class: Type[BaseExporter], override: bool = False
    ) -> None:
        """
        Register an exporter class.

        Args:
            exporter_class: Exporter class to register
            override: Whether to override existing registration

        Raises:
            ValueError: If exporter name conflicts and override=False
        """
        # Get name from class
        name = exporter_class.name if hasattr(exporter_class, "name") else None

        if name is None:
            raise ValueError(
                f"Exporter class {exporter_class.__name__} must define 'name' property"
            )

        if name in self._exporters and not override:
            raise ValueError(
                f"Exporter '{name}' already registered. Use override=True to replace."
            )

        self._exporters[name] = exporter_class
        logger.info(f"Registered exporter: {name}")

    def get(self, name: str) -> Optional[Type[BaseExporter]]:
        """
        Get exporter class by name.

        Args:
            name: Exporter name

        Returns:
            Exporter class or None if not found
        """
        return self._exporters.get(name)

    def list_exporters(self) -> List[str]:
        """
        List all registered exporter names.

        Returns:
            List of exporter names
        """
        return list(self._exporters.keys())

    def create_exporter(
        self, name: str, config: Dict[str, Any], enabled: bool = True
    ) -> Optional[BaseExporter]:
        """
        Create an exporter instance.

        Args:
            name: Exporter name
            config: Configuration dictionary
            enabled: Whether exporter should be enabled

        Returns:
            Configured exporter instance or None if not found
        """
        exporter_class = self.get(name)
        if exporter_class is None:
            logger.error(f"Exporter '{name}' not found in registry")
            return None

        try:
            exporter = exporter_class(enabled=enabled)
            exporter.configure(config)
            return exporter
        except Exception as e:
            logger.error(
                f"Failed to create exporter '{name}': {e}", exc_info=True
            )
            return None


class ExporterFactory:
    """
    Factory for creating and managing multiple exporters.

    Enables:
    - Creating exporters from configuration
    - Managing multiple simultaneous exporters
    - Aggregating span processors and metric readers
    - Health monitoring across all exporters
    """

    def __init__(self, registry: Optional[ExporterRegistry] = None):
        """
        Initialize the factory.

        Args:
            registry: Exporter registry (creates new if None)
        """
        self.registry = registry or ExporterRegistry()
        self._exporters: List[BaseExporter] = []

    def create_from_config(
        self, exporters_config: List[Dict[str, Any]]
    ) -> List[BaseExporter]:
        """
        Create exporters from configuration list.

        Args:
            exporters_config: List of exporter configurations
                Each config must have 'name' and 'enabled' keys

        Returns:
            List of created exporters

        Example:
            exporters_config = [
                {
                    "name": "splunk",
                    "enabled": True,
                    "config": {"token": "...", "url": "..."}
                },
                {
                    "name": "dynatrace",
                    "enabled": True,
                    "config": {"api_token": "...", "environment": "..."}
                }
            ]
        """
        exporters = []

        for exporter_cfg in exporters_config:
            name = exporter_cfg.get("name")
            enabled = exporter_cfg.get("enabled", True)
            config = exporter_cfg.get("config", {})

            if not name:
                logger.warning("Exporter configuration missing 'name', skipping")
                continue

            exporter = self.registry.create_exporter(name, config, enabled)
            if exporter:
                exporters.append(exporter)
                logger.info(f"Created exporter: {name} (enabled={enabled})")

        self._exporters = exporters
        return exporters

    def get_all_span_processors(self) -> List[SpanProcessor]:
        """
        Get span processors from all enabled exporters.

        Returns:
            List of span processors
        """
        processors = []
        for exporter in self._exporters:
            if exporter.enabled:
                try:
                    processor = exporter.get_span_processor()
                    processors.append(processor)
                except Exception as e:
                    logger.error(
                        f"Failed to get span processor from {exporter.name}: {e}",
                        exc_info=True,
                    )
        return processors

    def get_all_metric_readers(self) -> List[MetricReader]:
        """
        Get metric readers from all enabled exporters.

        Returns:
            List of metric readers
        """
        readers = []
        for exporter in self._exporters:
            if exporter.enabled:
                try:
                    reader = exporter.get_metric_reader()
                    readers.append(reader)
                except Exception as e:
                    logger.error(
                        f"Failed to get metric reader from {exporter.name}: {e}",
                        exc_info=True,
                    )
        return readers

    def health_check_all(self) -> Dict[str, bool]:
        """
        Run health checks on all exporters.

        Returns:
            Dictionary mapping exporter name to health status
        """
        results = {}
        for exporter in self._exporters:
            results[exporter.name] = exporter.health_check()
        return results

    def shutdown_all(self) -> None:
        """Shutdown all exporters."""
        for exporter in self._exporters:
            try:
                exporter.shutdown()
            except Exception as e:
                logger.error(
                    f"Error shutting down {exporter.name}: {e}", exc_info=True
                )


# Global registry instance
_global_registry = ExporterRegistry()


def get_global_registry() -> ExporterRegistry:
    """
    Get the global exporter registry.

    Returns:
        Global ExporterRegistry instance
    """
    return _global_registry


def register_exporter(
    exporter_class: Type[BaseExporter], override: bool = False
) -> None:
    """
    Register an exporter in the global registry.

    Args:
        exporter_class: Exporter class to register
        override: Whether to override existing registration
    """
    _global_registry.register(exporter_class, override=override)
