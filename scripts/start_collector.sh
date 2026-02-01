#!/bin/bash
# Start OpenTelemetry Collector for Linux/Mac
#
# Prerequisites:
#   - Download OpenTelemetry Collector from:
#     https://github.com/open-telemetry/opentelemetry-collector-releases/releases
#   - Extract to a directory (e.g., /opt/otel-collector)
#   - Update COLLECTOR_PATH below to point to the extracted directory
#   - Make this script executable: chmod +x start_collector.sh

# Configuration
COLLECTOR_PATH="/opt/otel-collector"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/../config/otel-collector-config.yaml"

# Check if collector exists
if [ ! -f "$COLLECTOR_PATH/otelcol" ]; then
    echo "ERROR: OpenTelemetry Collector not found at $COLLECTOR_PATH"
    echo ""
    echo "Please download the collector from:"
    echo "https://github.com/open-telemetry/opentelemetry-collector-releases/releases"
    echo ""
    echo "Extract it to $COLLECTOR_PATH or update COLLECTOR_PATH in this script."
    exit 1
fi

# Check if config exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: Configuration file not found at $CONFIG_FILE"
    exit 1
fi

echo "Starting OpenTelemetry Collector..."
echo "Config: $CONFIG_FILE"
echo ""

# Start collector
"$COLLECTOR_PATH/otelcol" --config "$CONFIG_FILE"
