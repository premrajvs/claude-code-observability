# 🙏 Credits & Attribution

## Original Project

This project builds upon the excellent work of:

### [Claude-Code-Usage-Monitor](https://github.com/Maciek-roboblog/Claude-Code-Usage-Monitor)

**Created by:** [@Maciek-roboblog](https://github.com/Maciek-roboblog)
**License:** MIT
**Stars:** 6,300+
**Description:** Beautiful real-time terminal monitoring tool for Claude AI token usage

---

## What We Reused

We've adapted and extended code from the original project:

### Core Modules Adapted:
1. **Data Reading Logic** (`reader.py`)
   - JSONL file parsing
   - Token extraction
   - Timestamp processing
   - Deduplication logic

2. **Data Models** (`models.py`)
   - UsageEntry dataclass
   - TokenCounts structure
   - SessionBlock model
   - Model name normalization

3. **Cost Calculations** (`pricing.py`)
   - Model-specific pricing
   - Cache token calculations
   - Cost aggregation

4. **Data Processing** (`data_processors.py`)
   - Token extraction
   - Timestamp conversion
   - Data validation

### Concepts & Algorithms:
- P90 percentile calculations
- Session block aggregation
- Burn rate calculations
- Multi-model support

---

## What We Added

### New Features (Not in Original):
1. **Phoenix AI Integration**
   - OpenTelemetry instrumentation
   - Web-based observability
   - Real-time visualization

2. **Conversation Analysis**
   - Full prompt/response parsing
   - Conversation history tracking
   - Project-level insights

3. **Quality Detection**
   - Hallucination detection algorithms
   - Error pattern recognition
   - Quality scoring

4. **Enhanced Monitoring**
   - File watching system
   - Background processing
   - Auto-refresh dashboard

5. **Additional Parsers**
   - `history.jsonl` parser (conversations)
   - `stats-cache.json` parser (aggregated stats)
   - Project analytics

---

## Contributors to Original Project

Thank you to all contributors to Claude-Code-Usage-Monitor:
- @Maciek-roboblog (Creator & Maintainer)
- All GitHub contributors and community members

*If you contributed to the original project and would like to be listed here, please open an issue!*

---

## Open Source Dependencies

### From Original Project:
- **Rich** - Terminal UI
- **Pydantic** - Data validation
- **Click** - CLI framework

### Added for Observatory:
- **Phoenix** - AI observability platform (Arize AI)
- **OpenTelemetry** - Telemetry framework (CNCF)
- **Watchdog** - File system monitoring
- **PyYAML** - Configuration

---

## License Compliance

This project is licensed under the **MIT License**, same as the original.

**MIT License allows:**
- ✅ Commercial use
- ✅ Modification
- ✅ Distribution
- ✅ Private use

**Requirements:**
- ✅ Include original license (we do)
- ✅ Include copyright notice (we do)
- ✅ State changes made (we do - see README)

---

## Giving Back

We encourage users to:

1. ⭐ **Star the original repo:** [Claude-Code-Usage-Monitor](https://github.com/Maciek-roboblog/Claude-Code-Usage-Monitor)

2. 💬 **Contribute back:** If you find bugs in the core parsing logic we use, please report them to the original project too

3. 🤝 **Collaborate:** We'd love to work with the original author and contributors

---

## Contact Original Author

If you're @Maciek-roboblog or a contributor to Claude-Code-Usage-Monitor:

- We'd love to collaborate!
- Open to merging efforts if interested
- Happy to contribute improvements back upstream
- Contact us via GitHub issues

---

## Acknowledgments

Special thanks to:
- **Anthropic** for Claude Code and the API
- **Arize AI** for Phoenix observability platform
- **The Python community** for excellent tools
- **Everyone who contributed** to the original Claude Monitor

---

**Built with ❤️ on the shoulders of giants**