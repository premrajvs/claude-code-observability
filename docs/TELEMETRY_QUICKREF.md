# OpenTelemetry Telemetry - Quick Reference

## Installation

```bash
# Install dependencies
pip install -e .

# Download collector (one-time)
# See docs/TELEMETRY_SETUP.md for download links
```

## Common Commands

### Start Telemetry Collection
```bash
python -m claude_monitor.cli.telemetry_command telemetry --enable
```

### Test Connection
```bash
python -m claude_monitor.cli.telemetry_command telemetry --test
```

### Start Collector
```bash
# Windows
scripts\start_collector.bat

# Linux/Mac
./scripts/start_collector.sh
```

### Custom Watch Directory
```bash
python -m claude_monitor.cli.telemetry_command telemetry --enable \
  --watch-dir /path/to/claude/logs
```

## Environment Variables

```bash
# Service identification
export OTEL_SERVICE_NAME="claude-monitor"
export DEPLOYMENT_ENVIRONMENT="production"

# Collector
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4318"

# Splunk (for direct mode)
export SPLUNK_HEC_TOKEN="your-token"
export SPLUNK_HEC_URL="http://localhost:8088/services/collector"
```

## Splunk Queries

### Session Summary
```spl
index=main sourcetype=_json service.name="claude-monitor"
| stats count as messages, sum(tokens.total) as tokens, sum(cost.usd) as cost by session.id
| sort - cost
```

### Token Usage by Model
```spl
index=main sourcetype=_json
| timechart sum(tokens.total) by model
```

### Tool Usage
```spl
index=main sourcetype=_json message.type="tool_use"
| stats count by tool.name
| sort - count
```

### Expensive Sessions
```spl
index=main sourcetype=_json
| stats sum(cost.usd) as total_cost by session.id
| where total_cost > 1.0
| sort - total_cost
```

### Hourly Cost
```spl
index=main sourcetype=_json
| bucket _time span=1h
| stats sum(cost.usd) as cost by _time
| sort - _time
```

## Programmatic Usage

```python
from claude_monitor.telemetry import (
    initialize_telemetry,
    ClaudeLogWatcher,
    shutdown_telemetry
)
from claude_monitor.telemetry.event_transformer import OTelTransformer
from claude_monitor.telemetry.session_tracker import SessionTracker
from claude_monitor.telemetry.models import TelemetryConfig

# Initialize
config = TelemetryConfig.from_env()
tracer, meter = initialize_telemetry(config)

# Create components
transformer = OTelTransformer(tracer, meter)
tracker = SessionTracker(tracer)
watcher = ClaudeLogWatcher(transformer, tracker)

# Run
watcher.run()  # Blocks until stopped

# Cleanup
shutdown_telemetry()
```

## Troubleshooting

### No Data in Splunk
1. Check collector is running: `ps aux | grep otelcol`
2. Check collector logs for errors
3. Verify Splunk HEC token in config
4. Test connection: `telemetry --test`

### Collector Won't Start
1. Check ports: `netstat -an | grep 4318`
2. Validate config: `otelcol --config config/otel-collector-config.yaml --dry-run`
3. Check logs in collector output

### High Memory Usage
Reduce batch size in `config/otel-collector-config.yaml`:
```yaml
processors:
  batch:
    send_batch_size: 50  # Default: 100
```

## Configuration Files

| File | Purpose |
|------|---------|
| `config/otel-collector-config.yaml` | Collector configuration |
| `pyproject.toml` | Python dependencies |
| `scripts/start_collector.bat` | Windows collector helper |
| `scripts/start_collector.sh` | Linux/Mac collector helper |

## Key Metrics

| Metric | Description |
|--------|-------------|
| `claude.tokens.input` | Input tokens |
| `claude.tokens.output` | Output tokens |
| `claude.tokens.total` | All tokens |
| `claude.cost.total` | Total cost (USD) |
| `claude.tools.usage` | Tool usage count |
| `claude.messages.count` | Message count |

## Span Attributes

| Attribute | Example |
|-----------|---------|
| `session.id` | `7d826144-bcb1-...` |
| `message.type` | `user`, `assistant`, `tool_use` |
| `model` | `claude-sonnet-4-5-20250929` |
| `tokens.total` | `1850` |
| `cost.usd` | `0.0245` |
| `tool.name` | `Read`, `Bash`, `Grep` |

## Switch to Dynatrace

1. Edit `config/otel-collector-config.yaml`:
```yaml
exporters:
  otlp/dynatrace:
    endpoint: "https://{env-id}.live.dynatrace.com/api/v2/otlp"
    headers:
      Authorization: "Api-Token YOUR_TOKEN"

service:
  pipelines:
    traces:
      exporters: [otlp/dynatrace, logging]
    metrics:
      exporters: [otlp/dynatrace, logging]
```

2. Restart collector
3. Done! No code changes needed.

## Documentation

- Setup Guide: `docs/TELEMETRY_SETUP.md`
- Implementation: `docs/TELEMETRY_README.md`
- Summary: `IMPLEMENTATION_SUMMARY.md`
- Example: `examples/telemetry_example.py`

## Performance

- CPU: 2-5% per session
- Memory: 50-100MB base + 10MB/1K events
- Network: Batched every 10s
- Latency: <100ms per event

## Support

For issues or questions:
1. Check `docs/TELEMETRY_SETUP.md` troubleshooting section
2. Review collector logs
3. Test with `telemetry --test`
4. Check Splunk HEC connection manually
