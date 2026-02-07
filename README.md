# Claude Code Observatory

Monitor Claude Code usage with OpenTelemetry and Splunk. Track tokens, costs, sessions, and tool usage.

## Quick Start

### 1. Install OpenTelemetry Collector

Install as Windows service:
```powershell
msiexec /i "https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v0.145.0/otelcol-contrib_0.145.0_windows_x64.msi"
```

**Important**: Use `contrib` version (includes Splunk HEC exporter).

### 2. Enable Splunk HEC

1. Open Splunk Web: `http://localhost:8000`
2. **Settings → Data Inputs → HTTP Event Collector → Global Settings**
   - Enable: **All Tokens**
   - Port: **8088**
   - SSL: **Disabled** (for local testing)
3. Create HEC token and copy it

### 3. Create Splunk Index

**Settings → Indexes → New Index**
- Name: `idx-claudecode`

### 4. Configure Collector

```powershell
# Copy config to service location
copy otel-collector-config.yaml "C:\Program Files\OpenTelemetry Collector\config.yaml"
```

Edit `C:\Program Files\OpenTelemetry Collector\config.yaml`:
- Update HEC token (line 69)
- Update index name to `idx-claudecode` (line 72)

```powershell
# Restart service
Restart-Service otelcol
```

### 5. Start Monitoring

```powershell
cd C:\Users\premr\claude-code-observatory
.\venv\Scripts\python.exe -m claude_monitor.cli.telemetry_command telemetry --enable
```

### 6. Query in Splunk

```spl
index=idx-claudecode
```

## Architecture

```
Claude Code (.jsonl logs)
    ↓
Python Telemetry Collector
    ↓ OTLP/HTTP (port 4318)
OpenTelemetry Collector (Windows Service)
    ↓ Splunk HEC (port 8088)
Splunk Enterprise
```

## Splunk Queries

### Session Summary
```spl
index=idx-claudecode
| stats count as messages,
        sum(tokens.total) as tokens,
        sum(cost.usd) as cost
  by session.id
| sort - cost
```

### Token Usage Over Time
```spl
index=idx-claudecode
| timechart sum(tokens.total) by model
```

### Tool Usage
```spl
index=idx-claudecode message.type="tool_use"
| stats count by tool.name
| sort - count
```

### Daily Cost
```spl
index=idx-claudecode
| bucket _time span=1d
| stats sum(cost.usd) as daily_cost by _time
| sort - _time
```

More queries in `SPLUNK_QUERIES.md`.

## Configuration Files

| File | Purpose |
|------|---------|
| `C:\Program Files\OpenTelemetry Collector\config.yaml` | Collector service config |
| `otel-collector-config.yaml` | Repository template |
| `config.yaml` | Observatory settings |

## Troubleshooting

### No data in Splunk?

1. **Check collector health**:
   ```powershell
   curl http://localhost:13133
   ```

2. **Check data flow**:
   ```powershell
   curl http://localhost:8888/metrics | findstr "receiver_accepted"
   ```

3. **Verify HEC**:
   ```powershell
   curl http://localhost:8088/services/collector/health
   ```

4. **Check index exists**: Settings → Indexes in Splunk

### Service Issues

```powershell
# Check service status
Get-Service otelcol

# Restart service
Restart-Service otelcol

# Check if port is in use
netstat -ano | findstr :8888
```

## Documentation

- **Setup Guide**: `docs/TELEMETRY_SETUP.md` - Detailed installation
- **Quick Reference**: `docs/TELEMETRY_QUICKREF.md` - Common commands
- **Troubleshooting**: See TELEMETRY_SETUP.md

## Project Structure

```
src/claude_monitor/
├── telemetry/
│   ├── otel_setup.py           # OpenTelemetry SDK setup
│   ├── event_transformer.py    # JSONL → OTel transformation
│   ├── file_watcher.py         # Watch Claude logs
│   └── session_tracker.py      # Session span management
└── cli/
    └── telemetry_command.py    # CLI interface
```

## Credits

Built on [Claude Code Usage Monitor](https://github.com/Maciek-roboblog/Claude-Code-Usage-Monitor) by @Maciek-roboblog

## License

MIT
