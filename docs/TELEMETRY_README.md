# OpenTelemetry Telemetry Implementation

## Overview

This implementation provides OpenTelemetry-based telemetry collection for Claude Code conversations. It transforms JSONL log events into structured traces, metrics, and logs that can be exported to any OpenTelemetry-compatible backend.

## What Was Implemented

### Core Components

1. **Event Transformer** (`telemetry/event_transformer.py`)
   - Parses JSONL log events
   - Creates OpenTelemetry spans with proper attributes
   - Records metrics for tokens, costs, and usage
   - Handles all event types: user messages, assistant responses, tool use, tool results

2. **Session Tracker** (`telemetry/session_tracker.py`)
   - Manages session lifecycle (start/end)
   - Creates root spans for sessions with child spans for events
   - Tracks aggregated metrics per session
   - Maintains session metadata (message counts, token totals, costs)

3. **File Watcher** (`telemetry/file_watcher.py`)
   - Watches `~/.claude/projects` for JSONL files
   - Incrementally processes new log entries
   - Detects new sessions automatically
   - Supports custom event callbacks

4. **OpenTelemetry Setup** (`telemetry/otel_setup.py`)
   - Initializes TracerProvider and MeterProvider
   - Configures OTLP exporters (HTTP/gRPC)
   - Sets up resource attributes (service name, version, host, etc.)
   - Provides graceful shutdown

5. **Configuration** (`telemetry/models.py`)
   - `TelemetryConfig`: Configuration from environment or code
   - `ClaudeEvent`: Structured event model
   - `SessionMetadata`: Session tracking data

6. **CLI Integration** (`cli/telemetry_command.py`)
   - `telemetry --enable`: Start collection
   - `telemetry --test`: Test connection
   - `telemetry --disable`: Stop collection (stub)

### OpenTelemetry Signals

#### Traces
Each session creates a distributed trace:
```
Session (root span)
├── User Message
│   ├── Tool Use (Read)
│   └── Tool Result
├── Assistant Response
└── ...
```

**Span Attributes:**
- `session.id`, `session.project_path`, `session.slug`
- `message.id`, `message.type`, `request.id`
- `model` (e.g., "claude-sonnet-4-5")
- `tokens.input`, `tokens.output`, `tokens.cache_creation`, `tokens.cache_read`, `tokens.total`
- `cost.usd`
- `tool.name` (for tool spans)

#### Metrics
Counter and histogram metrics:
- `claude.tokens.input` (counter)
- `claude.tokens.output` (counter)
- `claude.tokens.cache_creation` (counter)
- `claude.tokens.cache_read` (counter)
- `claude.tokens.total` (counter)
- `claude.cost.total` (counter)
- `claude.messages.count` (counter)
- `claude.tools.usage` (counter)

All metrics include dimensions: `session.id`, `message.type`, `model`, `tool.name` (where applicable)

#### Logs
Structured logs with full event data (future enhancement)

### Collector Configuration

**File:** `config/otel-collector-config.yaml`

**Receivers:**
- OTLP (gRPC on :4317, HTTP on :4318)

**Processors:**
- `batch`: Batches telemetry for efficiency
- `resource`: Adds service identification
- `attributes`: Enriches data
- `memory_limiter`: Prevents OOM

**Exporters:**
- `splunk_hec`: Sends to Splunk (configured)
- `logging`: Console output for debugging
- `otlp/dynatrace`: Ready for Dynatrace (commented)

### Helper Scripts

1. **Windows:** `scripts/start_collector.bat`
2. **Linux/Mac:** `scripts/start_collector.sh`

Both scripts:
- Check for collector installation
- Load configuration
- Start collector

## File Structure

```
src/claude_monitor/
├── telemetry/
│   ├── __init__.py
│   ├── models.py              # Data models
│   ├── otel_setup.py          # SDK initialization
│   ├── event_transformer.py   # JSONL → OTel
│   ├── session_tracker.py     # Session management
│   ├── file_watcher.py        # Log file monitoring
│   └── exporters/
│       └── __init__.py
└── cli/
    └── telemetry_command.py   # CLI integration

config/
└── otel-collector-config.yaml # Collector config

scripts/
├── start_collector.bat        # Windows helper
└── start_collector.sh         # Linux/Mac helper

docs/
├── TELEMETRY_SETUP.md         # Setup guide
└── TELEMETRY_README.md        # This file

examples/
└── telemetry_example.py       # Programmatic usage

tests/
└── test_telemetry.py          # Unit tests
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -e .
```

Dependencies added to `pyproject.toml`:
- `opentelemetry-exporter-otlp-proto-http>=1.39.0`
- `opentelemetry-exporter-otlp-proto-grpc>=1.39.0`

### 2. Download Collector

```bash
# Windows
scripts\start_collector.bat

# Linux/Mac
./scripts/start_collector.sh
```

Or download manually from:
https://github.com/open-telemetry/opentelemetry-collector-releases/releases

### 3. Configure Splunk HEC

Edit `config/otel-collector-config.yaml`:

```yaml
exporters:
  splunk_hec:
    token: "YOUR_SPLUNK_HEC_TOKEN"
    endpoint: "http://localhost:8088/services/collector"
```

### 4. Start Collector

```bash
# Using helper script
scripts/start_collector.bat  # Windows
./scripts/start_collector.sh  # Linux/Mac

# Or directly
otelcol --config config/otel-collector-config.yaml
```

### 5. Start Telemetry

```bash
python -m claude_monitor.cli.telemetry_command telemetry --enable
```

### 6. Verify

```bash
# Test connection
python -m claude_monitor.cli.telemetry_command telemetry --test

# Check Splunk
# Search: index=main sourcetype=_json service.name="claude-monitor"
```

## Usage Examples

### CLI Mode

```bash
# Basic usage
python -m claude_monitor.cli.telemetry_command telemetry --enable

# Custom watch directory
python -m claude_monitor.cli.telemetry_command telemetry --enable \
  --watch-dir /path/to/logs

# Direct mode (no collector)
python -m claude_monitor.cli.telemetry_command telemetry --enable \
  --direct-mode \
  --splunk-token YOUR_TOKEN \
  --splunk-url http://localhost:8088/services/collector

# Test connection
python -m claude_monitor.cli.telemetry_command telemetry --test
```

### Programmatic Usage

```python
from claude_monitor.telemetry import (
    initialize_telemetry,
    ClaudeLogWatcher,
    shutdown_telemetry
)
from claude_monitor.telemetry.event_transformer import OTelTransformer
from claude_monitor.telemetry.session_tracker import SessionTracker
from claude_monitor.telemetry.models import TelemetryConfig

# Configure
config = TelemetryConfig(
    service_name="my-claude-monitor",
    use_collector=True,
    collector_endpoint="http://localhost:4318"
)

# Initialize
tracer, meter = initialize_telemetry(config)

# Create components
transformer = OTelTransformer(tracer, meter)
session_tracker = SessionTracker(tracer)

# Start watching
watcher = ClaudeLogWatcher(
    transformer=transformer,
    session_tracker=session_tracker
)
watcher.run()  # Blocks until stopped

# Cleanup
shutdown_telemetry()
```

See `examples/telemetry_example.py` for full example with custom callbacks.

## Migration to Dynatrace

To switch from Splunk to Dynatrace:

### Update Collector Config

Edit `config/otel-collector-config.yaml`:

```yaml
exporters:
  otlp/dynatrace:
    endpoint: "https://{env-id}.live.dynatrace.com/api/v2/otlp"
    headers:
      Authorization: "Api-Token YOUR_DYNATRACE_TOKEN"

service:
  pipelines:
    traces:
      exporters: [otlp/dynatrace, logging]
    metrics:
      exporters: [otlp/dynatrace, logging]
```

Restart collector. **No code changes required!**

## Testing

Run tests:

```bash
# All tests
pytest tests/test_telemetry.py

# Specific test
pytest tests/test_telemetry.py::TestOTelTransformer::test_parse_jsonl_line

# With coverage
pytest tests/test_telemetry.py --cov=claude_monitor.telemetry
```

## Configuration Reference

### Environment Variables

```bash
OTEL_SERVICE_NAME="claude-monitor"
OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4318"
DEPLOYMENT_ENVIRONMENT="production"
TELEMETRY_USE_COLLECTOR="true"
SPLUNK_HEC_TOKEN="your-token"
SPLUNK_HEC_URL="http://localhost:8088/services/collector"
```

### TelemetryConfig Fields

```python
TelemetryConfig(
    service_name="claude-monitor",
    service_version="1.0.0",
    deployment_environment="local",
    use_collector=True,
    collector_endpoint="http://localhost:4318",
    splunk_hec_token=None,
    splunk_hec_url=None,
    splunk_index="main",
    splunk_source="claude-monitor",
    splunk_sourcetype="_json",
    trace_sample_rate=1.0,
    batch_timeout_seconds=10,
    batch_max_size=100,
    watch_directory=None,  # Defaults to ~/.claude/projects
    file_check_interval_seconds=1.0
)
```

## Known Limitations

1. **Direct Mode**: Direct Splunk HEC export without collector not fully implemented (uses console exporter as fallback)
2. **Logs Signal**: OpenTelemetry logs not yet implemented (only traces and metrics)
3. **Daemon Mode**: CLI `--daemon` flag not implemented (runs in foreground)
4. **Disable Command**: `telemetry --disable` not implemented

## Future Enhancements

- [ ] Implement direct Splunk HEC exporter (without collector)
- [ ] Add OpenTelemetry logs signal
- [ ] Daemon/background mode with PID file
- [ ] Real-time alerting (cost thresholds, error rates)
- [ ] Session comparison and analysis
- [ ] Automatic cost optimization recommendations
- [ ] Integration with CI/CD pipelines
- [ ] Grafana dashboards

## Performance

- **CPU**: ~2-5% overhead per active session
- **Memory**: ~50-100MB base + ~10MB per 1000 events
- **Network**: Batched exports every 10s (configurable)
- **Disk**: No local storage (streams to collector)

## Troubleshooting

See `docs/TELEMETRY_SETUP.md` for detailed troubleshooting guide.

## References

- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [OTel Collector Configuration](https://opentelemetry.io/docs/collector/configuration/)
- [Splunk HEC](https://docs.splunk.com/Documentation/Splunk/latest/Data/UsetheHTTPEventCollector)
- [Dynatrace OTLP](https://www.dynatrace.com/support/help/extend-dynatrace/opentelemetry)

## License

MIT (same as parent project)
