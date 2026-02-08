# OpenTelemetry Telemetry Setup Guide

Quick setup guide for monitoring Claude Code usage with OpenTelemetry and Splunk.

## Prerequisites

- Python 3.9+ with dependencies installed (`pip install -e .`)
- Splunk Enterprise running locally
- OpenTelemetry Collector Contrib installed as Windows service

## Step 1: Install OpenTelemetry Collector

Install as Windows service using the MSI installer:

```powershell
msiexec /i "https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v0.145.0/otelcol-contrib_0.145.0_windows_x64.msi"
```

**Important:** Install the **contrib** version (not core) - it includes the Splunk HEC exporter.

## Step 2: Enable Splunk HEC

1. Open Splunk Web: `http://localhost:8000`
2. Go to **Settings → Data Inputs → HTTP Event Collector**
3. Click **Global Settings**:
   - Enable: **All Tokens** (toggle to Enabled)
   - **HTTP Port Number**: `8088`
   - **Enable SSL**: Disabled (for local testing)
   - Click **Save**

4. Create a new HEC token:
   - Click **New Token**
   - **Name**: `Claude Observatory`
   - **Source**: `claude:observatory`
   - **Index**: Select your index (e.g., `idx-claudecode`)
   - Click **Review → Submit**
   - **Copy the token** - you'll need it for the config

5. Verify HEC is working:
   ```bash
   curl http://localhost:8088/services/collector/health
   ```
   Should return: `{"text":"HEC is healthy","code":17}`

## Step 3: Create Splunk Index

1. Go to **Settings → Indexes**
2. Click **New Index**
3. **Index Name**: `idx-claudecode` (or your preferred name)
4. Click **Save**

## Step 4: Configure the Collector

Copy your config to the service location:

```powershell
copy otel-collector-config.yaml "C:\Program Files\OpenTelemetry Collector\config.yaml"
```

**Edit the config** at `C:\Program Files\OpenTelemetry Collector\config.yaml`:

1. Update the **HEC token** (line 69):
   ```yaml
   token: "YOUR_HEC_TOKEN_HERE"
   ```

2. Update the **index name** (line 72):
   ```yaml
   index: "idx-claudecode"  # Use your index name
   ```

3. Ensure you have **three pipelines** (traces, metrics, logs):
   ```yaml
   service:
     pipelines:
       traces:
         receivers: [otlp]
         processors: [memory_limiter, batch, resource, attributes]
         exporters: [splunk_hec, debug]

       metrics:
         receivers: [otlp]
         processors: [memory_limiter, batch, resource]
         exporters: [splunk_hec, debug]

       logs:
         receivers: [otlp]
         processors: [memory_limiter, batch, resource]
         exporters: [splunk_hec, debug]
   ```

## Step 5: Restart the Collector Service

```powershell
Restart-Service otelcol
```

Verify it's running:
```powershell
curl http://localhost:13133
```
Should return: `{"status":"Server available",...}`

## Step 6: Start Telemetry Collection

```powershell
cd C:\Users\premr\claude-code-observatory
.\venv\Scripts\python.exe -m claude_monitor.cli.telemetry_command telemetry --enable
```

This will:
- Watch `C:\Users\premr\.claude\projects` for Claude Code logs
- Process existing and new conversation files
- Send telemetry to the collector
- Export to Splunk HEC

**Leave it running** while you use Claude Code.

## Step 7: Verify Data in Splunk

Search in Splunk:

```spl
index=idx-claudecode
```

You should see:
- Traces with session information
- Metrics for token usage
- Logs of conversation events

## Troubleshooting

### No data in Splunk?

1. **Check collector is receiving data**:
   ```bash
   curl http://localhost:8888/metrics | findstr "receiver_accepted"
   ```
   Should show `receiver_accepted_spans` > 0

2. **Check HEC is enabled**:
   ```bash
   curl http://localhost:8088/services/collector/health
   ```

3. **Verify index exists**: Settings → Indexes in Splunk

4. **Check HEC token is correct** in the collector config

5. **Search all indexes**:
   ```spl
   index=* source="claude:observatory"
   ```

### Service won't start?

Check if port 8888 is already in use:
```powershell
netstat -ano | findstr :8888
```

If another collector is running, stop it first.

## Configuration Files

- **Collector config**: `C:\Program Files\OpenTelemetry Collector\config.yaml`
- **Repository config**: `C:\Users\premr\claude-code-observatory\otel-collector-config.yaml`
- **Claude logs**: `C:\Users\premr\.claude\projects\**\*.jsonl`

## Next Steps

- Create Splunk dashboards for visualization
- Set up alerts on cost thresholds
- Analyze token usage patterns
- Track tool usage statistics
