# OpenTelemetry Telemetry Setup Guide

This guide explains how to set up and use the OpenTelemetry-based telemetry system for Claude Code monitoring.

## Overview

The telemetry system collects Claude Code conversation logs and exports them as:
- **Traces**: Distributed traces showing session flows and tool usage
- **Metrics**: Token counts, costs, and performance metrics
- **Logs**: Structured event logs

Data flows through the OpenTelemetry Collector to your observability backend (Splunk, Dynatrace, etc.).

## Architecture

```
Claude Code Logs (.jsonl)
    ↓
File Watcher (watchdog)
    ↓
OpenTelemetry SDK
    ↓
OTel Collector
    ↓
Backend (Splunk/Dynatrace/etc.)
```

## Prerequisites

1. **Python 3.9+** with dependencies installed:
   ```bash
   pip install -e .
   ```

2. **OpenTelemetry Collector** (recommended):
   - Download from: https://github.com/open-telemetry/opentelemetry-collector-releases/releases
   - Choose the appropriate version for your OS
   - Extract to a directory (e.g., `C:\otel-collector` on Windows)

3. **Observability Backend**:
   - Splunk with HEC enabled, OR
   - Dynatrace, OR
   - Any OTLP-compatible backend

## Installation

### Step 1: Install Dependencies

Dependencies are already included in `pyproject.toml`:
- `opentelemetry-api>=1.39.0`
- `opentelemetry-sdk>=1.39.0`
- `opentelemetry-exporter-otlp>=1.39.0`
- `watchdog>=3.0.0`

If needed, add the HTTP/gRPC exporters:
```bash
pip install opentelemetry-exporter-otlp-proto-http opentelemetry-exporter-otlp-proto-grpc
```

### Step 2: Download OpenTelemetry Collector

#### Windows:
```powershell
# Download the collector
$version = "0.93.0"  # Check for latest version
$url = "https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v$version/otelcol_${version}_windows_amd64.tar.gz"
Invoke-WebRequest -Uri $url -OutFile otelcol.tar.gz

# Extract
tar -xzf otelcol.tar.gz -C C:\otel-collector
```

#### Linux/Mac:
```bash
# Download the collector
VERSION="0.93.0"  # Check for latest version
curl -LO "https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v${VERSION}/otelcol_${VERSION}_linux_amd64.tar.gz"

# Extract
sudo mkdir -p /opt/otel-collector
sudo tar -xzf otelcol_${VERSION}_linux_amd64.tar.gz -C /opt/otel-collector
```

### Step 3: Configure the Collector

The collector configuration is in `config/otel-collector-config.yaml`. Key settings:

```yaml
exporters:
  splunk_hec:
    token: "YOUR_SPLUNK_HEC_TOKEN"
    endpoint: "http://localhost:8088/services/collector"
```

**Update the Splunk HEC token** in the config file or use environment variables:

```bash
export SPLUNK_HEC_TOKEN="your-token-here"
export SPLUNK_HEC_URL="http://localhost:8088/services/collector"
```

### Step 4: Start the Collector

#### Windows:
```cmd
scripts\start_collector.bat
```

Or manually:
```cmd
C:\otel-collector\otelcol.exe --config config\otel-collector-config.yaml
```

#### Linux/Mac:
```bash
chmod +x scripts/start_collector.sh
./scripts/start_collector.sh
```

Or manually:
```bash
/opt/otel-collector/otelcol --config config/otel-collector-config.yaml
```

You should see output like:
```
2024-01-30T12:00:00.000Z	info	service/service.go:123	Starting otelcol...
2024-01-30T12:00:00.000Z	info	service/service.go:145	Everything is ready. Begin running and processing data.
```

## Usage

### Start Telemetry Collection

```bash
python -m claude_monitor.cli.telemetry_command telemetry --enable
```

This will:
1. Initialize OpenTelemetry SDK
2. Start watching `~/.claude/projects` for JSONL files
3. Process existing logs and new events
4. Export traces and metrics to the collector

**Output:**
```
Starting Claude Monitor Telemetry
Initializing OpenTelemetry (mode: collector)
Watching directory: C:\Users\username\.claude\projects
Processing existing log files
Telemetry collection started successfully!

Press Ctrl+C to stop
```

### Test Connection

Test that telemetry is working:

```bash
python -m claude_monitor.cli.telemetry_command telemetry --test
```

This sends sample traces and metrics to verify the connection.

### Custom Watch Directory

Monitor a different directory:

```bash
python -m claude_monitor.cli.telemetry_command telemetry --enable --watch-dir /path/to/logs
```

### Direct Mode (Without Collector)

Send directly to Splunk HEC (not recommended):

```bash
python -m claude_monitor.cli.telemetry_command telemetry --enable --direct-mode \
  --splunk-token YOUR_TOKEN \
  --splunk-url http://localhost:8088/services/collector
```

## Configuration

### Environment Variables

```bash
# Service identification
export OTEL_SERVICE_NAME="claude-monitor"
export DEPLOYMENT_ENVIRONMENT="production"

# Collector endpoint
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4318"

# Splunk HEC (for direct mode)
export SPLUNK_HEC_TOKEN="your-token"
export SPLUNK_HEC_URL="http://localhost:8088/services/collector"

# Telemetry mode
export TELEMETRY_USE_COLLECTOR="true"  # or "false" for direct mode
```

### Configuration File

Edit `config/otel-collector-config.yaml` to:
- Change export destinations
- Add processors for filtering/enrichment
- Configure batching and retry behavior
- Enable multiple exporters

## Verifying Data

### Check Collector Logs

The collector should show data being received and exported:

```
2024-01-30T12:05:00.000Z	info	TracesExporter	{"#spans": 5}
2024-01-30T12:05:00.000Z	info	MetricsExporter	{"#metrics": 12}
```

### Splunk Queries

Search for Claude Monitor data in Splunk:

```spl
# All telemetry
index=main sourcetype=_json service.name="claude-monitor"

# Session summary
index=main sourcetype=_json service.name="claude-monitor"
| stats count as messages, sum(tokens.total) as tokens, sum(cost.usd) as cost by session.id

# Token usage over time
index=main sourcetype=_json service.name="claude-monitor"
| timechart sum(tokens.total) by model

# Most expensive sessions
index=main sourcetype=_json service.name="claude-monitor"
| stats sum(cost.usd) as total_cost by session.id
| sort - total_cost
| head 10

# Tool usage
index=main sourcetype=_json message.type="tool_use"
| stats count by tool.name
| sort - count
```

## Switching to Dynatrace

To switch from Splunk to Dynatrace:

### Option 1: Update Collector Config (Recommended)

Edit `config/otel-collector-config.yaml`:

```yaml
exporters:
  otlp/dynatrace:
    endpoint: "https://{your-env-id}.live.dynatrace.com/api/v2/otlp"
    headers:
      Authorization: "Api-Token YOUR_DYNATRACE_TOKEN"

service:
  pipelines:
    traces:
      exporters: [otlp/dynatrace, logging]
    metrics:
      exporters: [otlp/dynatrace, logging]
    logs:
      exporters: [otlp/dynatrace, logging]
```

Restart the collector. **No code changes needed!**

### Option 2: Run Both Simultaneously

Send to both Splunk and Dynatrace:

```yaml
service:
  pipelines:
    traces:
      exporters: [splunk_hec, otlp/dynatrace, logging]
```

## Troubleshooting

### No Data Appearing

1. **Check collector is running**:
   ```bash
   # Should show otelcol process
   ps aux | grep otelcol  # Linux/Mac
   tasklist | findstr otelcol  # Windows
   ```

2. **Check collector logs** for errors:
   - Look for "connection refused" or "authentication failed"

3. **Verify watch directory**:
   ```bash
   ls ~/.claude/projects/*.jsonl
   ```

4. **Test connection**:
   ```bash
   python -m claude_monitor.cli.telemetry_command telemetry --test
   ```

### Collector Won't Start

1. **Check port conflicts**: Ensure ports 4317 (gRPC) and 4318 (HTTP) are free
   ```bash
   netstat -an | grep 4318
   ```

2. **Validate config**:
   ```bash
   otelcol --config config/otel-collector-config.yaml --dry-run
   ```

### High Memory Usage

Reduce batch sizes in `config/otel-collector-config.yaml`:

```yaml
processors:
  batch:
    timeout: 5s
    send_batch_size: 50  # Reduce from 100
```

## Advanced Usage

### Custom Event Processing

Create a custom event callback:

```python
from claude_monitor.telemetry import ClaudeLogWatcher, initialize_telemetry
from claude_monitor.telemetry.event_transformer import OTelTransformer
from claude_monitor.telemetry.session_tracker import SessionTracker

def my_event_handler(event):
    print(f"New event: {event.type} - {event.message_id}")
    if event.cost_usd > 1.0:
        print(f"HIGH COST EVENT: ${event.cost_usd}")

# Initialize
tracer, meter = initialize_telemetry()
transformer = OTelTransformer(tracer, meter)
tracker = SessionTracker(tracer)

# Create watcher with callback
watcher = ClaudeLogWatcher(
    transformer=transformer,
    session_tracker=tracker,
    event_callback=my_event_handler
)

watcher.run()
```

### Sampling

Reduce data volume by sampling in the collector:

```yaml
processors:
  probabilistic_sampler:
    sampling_percentage: 50  # Sample 50% of traces

service:
  pipelines:
    traces:
      processors: [probabilistic_sampler, batch, resource]
```

## Performance

- **CPU**: ~2-5% overhead per active session
- **Memory**: ~50-100MB base + ~10MB per 1000 events
- **Network**: Batched exports every 10s (configurable)

## Next Steps

- Set up Splunk dashboards for visualization
- Configure alerting on cost thresholds
- Explore trace visualization in Splunk APM
- Add custom metrics for your use cases

## Reference

- [OpenTelemetry Docs](https://opentelemetry.io/docs/)
- [OTel Collector Config](https://opentelemetry.io/docs/collector/configuration/)
- [Splunk HEC](https://docs.splunk.com/Documentation/Splunk/latest/Data/UsetheHTTPEventCollector)
- [Dynatrace OTLP](https://www.dynatrace.com/support/help/extend-dynatrace/opentelemetry)
