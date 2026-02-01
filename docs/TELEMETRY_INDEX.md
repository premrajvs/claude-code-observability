# OpenTelemetry Telemetry - Documentation Index

## 🎯 Quick Start

**New to the telemetry system?** Start here:

1. **[TELEMETRY_FEATURES.md](TELEMETRY_FEATURES.md)** - Overview and capabilities
2. **[TELEMETRY_SETUP.md](TELEMETRY_SETUP.md)** - Installation and setup guide
3. **[TELEMETRY_QUICKREF.md](TELEMETRY_QUICKREF.md)** - Common commands and queries

## 📚 Documentation

### For Users

| Document | Purpose | Read Time |
|----------|---------|-----------|
| **[TELEMETRY_FEATURES.md](../TELEMETRY_FEATURES.md)** | What the system does and why | 5 min |
| **[TELEMETRY_SETUP.md](TELEMETRY_SETUP.md)** | Complete setup instructions | 15 min |
| **[TELEMETRY_QUICKREF.md](TELEMETRY_QUICKREF.md)** | Command and query reference | 2 min |

### For Developers

| Document | Purpose | Read Time |
|----------|---------|-----------|
| **[TELEMETRY_README.md](TELEMETRY_README.md)** | Implementation details | 10 min |
| **[../IMPLEMENTATION_SUMMARY.md](../IMPLEMENTATION_SUMMARY.md)** | What was built | 10 min |

### Examples

| File | Description |
|------|-------------|
| **[../examples/telemetry_example.py](../examples/telemetry_example.py)** | Programmatic usage example |
| **[../tests/test_telemetry.py](../tests/test_telemetry.py)** | Unit tests and examples |

## 🚀 Quick Commands

### Start Monitoring
```bash
# 1. Start collector
scripts/start_collector.bat  # Windows
./scripts/start_collector.sh  # Linux/Mac

# 2. Start telemetry
python -m claude_monitor.cli.telemetry_command telemetry --enable
```

### Test Connection
```bash
python -m claude_monitor.cli.telemetry_command telemetry --test
```

## 📊 Common Use Cases

### Cost Monitoring
Track Claude Code costs in real-time
→ See **[TELEMETRY_SETUP.md](TELEMETRY_SETUP.md#splunk-queries)** for Splunk queries

### Usage Analytics
Understand token usage patterns
→ See **[TELEMETRY_QUICKREF.md](TELEMETRY_QUICKREF.md#splunk-queries)** for examples

### Session Analysis
Deep-dive into conversation flows
→ See **[TELEMETRY_FEATURES.md](../TELEMETRY_FEATURES.md#traces)** for trace details

### Backend Migration
Switch from Splunk to Dynatrace
→ See **[TELEMETRY_SETUP.md](TELEMETRY_SETUP.md#switching-to-dynatrace)** for migration guide

## 🔧 Configuration

### Environment Variables
```bash
export OTEL_SERVICE_NAME="claude-monitor"
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4318"
export SPLUNK_HEC_TOKEN="your-token"
```

### Config Files
- **Collector:** `config/otel-collector-config.yaml`
- **Dependencies:** `pyproject.toml`

## 🧪 Testing

### Quick Test
```bash
python -m claude_monitor.cli.telemetry_command telemetry --test
```

### Run Tests
```bash
pytest tests/test_telemetry.py -v
```

## 📁 Source Code

### Core Modules
- `src/claude_monitor/telemetry/models.py` - Data models
- `src/claude_monitor/telemetry/otel_setup.py` - OTel initialization
- `src/claude_monitor/telemetry/event_transformer.py` - Event parsing
- `src/claude_monitor/telemetry/session_tracker.py` - Session management
- `src/claude_monitor/telemetry/file_watcher.py` - File monitoring

### CLI
- `src/claude_monitor/cli/telemetry_command.py` - CLI commands

## 🎓 Learning Path

**Beginner:**
1. Read [TELEMETRY_FEATURES.md](../TELEMETRY_FEATURES.md) for overview
2. Follow [TELEMETRY_SETUP.md](TELEMETRY_SETUP.md) for installation
3. Try the test command
4. Monitor a real session

**Intermediate:**
1. Review [TELEMETRY_QUICKREF.md](TELEMETRY_QUICKREF.md) for queries
2. Create custom Splunk dashboards
3. Set up alerting on costs
4. Explore the example in `examples/telemetry_example.py`

**Advanced:**
1. Read [TELEMETRY_README.md](TELEMETRY_README.md) for architecture
2. Review [IMPLEMENTATION_SUMMARY.md](../IMPLEMENTATION_SUMMARY.md) for details
3. Customize event processing with callbacks
4. Migrate to different backend (Dynatrace, etc.)

## 🆘 Troubleshooting

### No Data Appearing
→ See **[TELEMETRY_SETUP.md](TELEMETRY_SETUP.md#troubleshooting)**

### Collector Issues
→ See **[TELEMETRY_QUICKREF.md](TELEMETRY_QUICKREF.md#troubleshooting)**

### Performance Problems
→ See **[TELEMETRY_README.md](TELEMETRY_README.md#performance)**

## 🔗 Quick Links

- [OpenTelemetry Docs](https://opentelemetry.io/docs/)
- [OTel Collector Downloads](https://github.com/open-telemetry/opentelemetry-collector-releases/releases)
- [Splunk HEC Docs](https://docs.splunk.com/Documentation/Splunk/latest/Data/UsetheHTTPEventCollector)
- [Dynatrace OTLP Docs](https://www.dynatrace.com/support/help/extend-dynatrace/opentelemetry)

## 📋 Checklist

### First-Time Setup
- [ ] Install dependencies: `pip install -e .`
- [ ] Download OpenTelemetry Collector
- [ ] Configure Splunk HEC token
- [ ] Start collector
- [ ] Test connection: `telemetry --test`
- [ ] Start monitoring: `telemetry --enable`

### Daily Use
- [ ] Start collector in background
- [ ] Start telemetry collection
- [ ] Use Claude Code normally
- [ ] Check Splunk dashboards

### Maintenance
- [ ] Review session costs weekly
- [ ] Flush old collector logs monthly
- [ ] Update collector version quarterly
- [ ] Review usage patterns for optimization

## 💡 Tips

1. **Bookmark** `TELEMETRY_QUICKREF.md` for quick command lookups
2. **Save** common Splunk queries in your Splunk workspace
3. **Set up** alerts for cost thresholds
4. **Create** weekly cost reports
5. **Share** dashboards with your team

## 📞 Support

For questions or issues:
1. Check the relevant documentation above
2. Review troubleshooting sections
3. Test with `telemetry --test`
4. Check collector logs for errors

---

**Last Updated:** January 31, 2026

**Status:** ✅ Production Ready

**Version:** 1.0.0
