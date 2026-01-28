# Claude Code Observatory

Monitor Claude Code usage with Splunk via OpenTelemetry. Track tokens, costs, sessions, and quality metrics.

## Quick Start

### 1. Install Splunk OTel Collector

PowerShell (as Administrator):
```powershell
& {Set-ExecutionPolicy Bypass -Scope Process -Force; iex ((New-Object System.Net.WebClient).DownloadString('https://dl.signalfx.com/splunk-otel-collector.ps1'))}
```

Choose `agent` mode, skip realm/token prompts.

### 2. Configure Collector

```powershell
Copy-Item otel-collector-config.yaml "C:\ProgramData\Splunk\OpenTelemetry Collector\agent_config.yaml"
Start-Service splunk-otel-collector
```

### 3. Create Splunk Index

In Splunk Web (http://localhost:8000):
- Settings → Indexes → New Index
- Name: `claude_observatory`

### 4. Run Observatory

```bash
cd src
python -m claude_observatory
```

### 5. Query in Splunk

```spl
index=claude_observatory sourcetype="otel:traces"
| stats count by openinference.span.kind
```

## Architecture

```
Claude Observatory (Python)
    ↓ OTLP/HTTP (port 4318)
OTel Collector
    ↓ Splunk HEC (port 8088)
Splunk Enterprise
```

## Configuration

Edit `config.yaml`:

```yaml
opentelemetry:
  endpoint: "http://localhost:4318/v1/traces"

splunk:
  hec_token: "your-token-here"
  index: "claude_observatory"
```

## Splunk Queries

### Token Usage by Project
```spl
index=claude_observatory openinference.span.kind="LLM"
| eval tokens=tonumber('llm.token_count.total')
| stats sum(tokens) by project.name
```

### Cost by Project
```spl
index=claude_observatory openinference.span.kind="LLM"
| eval cost=tonumber('llm.cost.total')
| stats sum(cost) as total_cost by project.name
| sort -total_cost
```

### Hourly Token Trend
```spl
index=claude_observatory openinference.span.kind="LLM"
| eval tokens=tonumber('llm.token_count.total')
| timechart span=1h sum(tokens) by project.name
```

### Session Quality
```spl
index=claude_observatory openinference.span.kind="CHAIN"
| stats avg(tonumber('session.quality_score')) as avg_quality,
        avg(tonumber('session.error_count')) as avg_errors
  by project.name
```

### Hallucination Events
```spl
index=claude_observatory openinference.span.kind="EVALUATOR"
| stats count by evaluation.category, project.name
```

More queries in `SPLUNK_QUERIES.md`.

## Data Schema

### LLM Spans
- `llm.model_name` - Model ID
- `llm.token_count.total` - Total tokens
- `llm.cost.total` - Cost in USD
- `project.name` - Project path
- `session.id` - Session UUID

### CHAIN Spans (Session Summary)
- `session.message_count` - Messages in session
- `session.total_tokens` - Total tokens used
- `session.total_cost` - Total cost
- `session.quality_score` - Quality (0-1)
- `session.error_count` - Number of errors

### EVALUATOR Spans (Quality)
- `evaluation.category` - Type (revert, error, etc.)
- `evaluation.confidence` - Confidence (0-1)
- `quality.issue_detected` - True/false

## Troubleshooting

### No data in Splunk?

Check collector status:
```powershell
Get-Service splunk-otel-collector
```

Test endpoint:
```powershell
Test-NetConnection -ComputerName localhost -Port 4318
```

View logs:
```powershell
Get-Content "C:\ProgramData\Splunk\OpenTelemetry Collector\logs\splunk-otel-collector.log" -Tail 50
```

### Collector config location

- Windows: `C:\ProgramData\Splunk\OpenTelemetry Collector\agent_config.yaml`
- Linux: `/etc/otel/collector/agent_config.yaml`

## Project Structure

```
src/claude_observatory/
├── otel_integration.py       # OpenTelemetry integration
├── session_parser.py          # Parse Claude sessions
├── hallucination_detector.py  # Quality detection
└── conversation_parser.py     # Parse conversation history
```

## Credits

Built on [Claude Code Usage Monitor](https://github.com/Maciek-roboblog/Claude-Code-Usage-Monitor) by @Maciek-roboblog

## License

MIT
