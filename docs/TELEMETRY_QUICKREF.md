# Telemetry Quick Reference

## Start Monitoring

```powershell
cd C:\Users\premr\claude-code-observatory
.\venv\Scripts\python.exe -m claude_monitor.cli.telemetry_command telemetry --enable
```

## Check Status

```powershell
# Collector health
curl http://localhost:13133

# Data flow metrics
curl http://localhost:8888/metrics | findstr "receiver_accepted"

# Splunk HEC health
curl http://localhost:8088/services/collector/health
```

## Manage Collector Service

```powershell
# Restart after config changes
Restart-Service otelcol

# Check service status
Get-Service otelcol
```

## Update Configuration

```powershell
# After editing otel-collector-config.yaml
copy otel-collector-config.yaml "C:\Program Files\OpenTelemetry Collector\config.yaml"
Restart-Service otelcol
```

## Splunk Searches

```spl
# All Claude data
index=idx-claudecode

# Session summary
index=idx-claudecode | stats count, sum(tokens.total) as tokens, sum(cost.usd) as cost by session.id

# Token usage over time
index=idx-claudecode | timechart sum(tokens.total) by model

# Tool usage
index=idx-claudecode message.type="tool_use" | stats count by tool.name | sort - count
```

## File Locations

- **Collector config**: `C:\Program Files\OpenTelemetry Collector\config.yaml`
- **Repository config**: `otel-collector-config.yaml`
- **Claude logs**: `C:\Users\premr\.claude\projects\**\*.jsonl`

## Common Issues

| Problem | Solution |
|---------|----------|
| No data in Splunk | Check HEC token and index name match in config |
| Port 8888 in use | Service already running, use `Restart-Service otelcol` |
| HEC 404/empty response | Enable HEC: Settings → Data Inputs → HTTP Event Collector |
| Data not sending | Verify index exists: Settings → Indexes |

## Documentation

- **Setup**: `docs/TELEMETRY_SETUP.md` - Full installation guide
- **Troubleshooting**: See TELEMETRY_SETUP.md
