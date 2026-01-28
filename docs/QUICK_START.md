# 🚀 Quick Start - Claude Code Observatory

## What This Does

**Claude Code Observatory** - Complete monitoring and observability for Claude Code:
- 📊 Token usage tracking with detailed breakdowns
- 💰 Automatic cost calculation by model
- 💬 Full conversation history analysis
- 🗂️ Multi-project support (monitor everything!)
- 🎭 Hallucination and error detection
- 🌐 Beautiful Phoenix AI web dashboard

Built on top of [Claude-Code-Usage-Monitor](https://github.com/Maciek-roboblog/Claude-Code-Usage-Monitor) (MIT License) by [@Maciek-roboblog](https://github.com/Maciek-roboblog)

---

## Installation (5 Minutes)

### Prerequisites
- Python 3.9+
- Claude Code CLI (with some usage history)

### Step 1: Clone and Install

```bash
cd C:\Users\premr\claude-code-observatory
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### Step 2: Run the Observatory

```bash
python start_observatory.py
```

### Step 3: Open Dashboard

Visit **http://localhost:6006** in your browser

---

## What It Monitors

### Automatically Discovers ALL Projects
- **`~/.claude/projects/`** - All your Claude Code projects
- Reads detailed session JSONL files
- Extracts token usage, costs, conversations, quality metrics
- No project-specific configuration needed!

### What You'll See
- ✅ Every session organized by time
- ✅ Token usage per message (input, output, cache)
- ✅ Cost breakdowns by model
- ✅ Session summaries and names
- ✅ Quality scores and error detection
- ✅ Project analytics

---

## Configuration (Optional)

Edit `config.yaml` to customize monitoring:

### Monitor ALL Projects (Default) ✅
```yaml
project_monitoring:
  mode: "all"
```
Automatically monitors everything in `~/.claude/projects/`

### Monitor Specific Projects Only
```yaml
project_monitoring:
  mode: "specific"
  specific_projects:
    - "C--Users-yourname-project1"
    - "C--Users-yourname-project2"
```

### Exclude Projects
```yaml
project_monitoring:
  mode: "all"
  exclude_projects:
    - "C--Users-yourname-test-project"
```

---

## Run in Background

### Linux/Mac
```bash
nohup python start_observatory.py > observatory.log 2>&1 &
```

### Windows
```powershell
start /B python start_observatory.py
```

---

## Key Features

### 🎯 Project-Agnostic Design
- No hardcoded paths
- Works with ANY Claude Code project
- Automatically discovers new projects
- Fully configurable via YAML

### 📊 Complete Token Tracking
- Input tokens
- Output tokens
- Cache creation (write) tokens
- Cache read tokens
- Total per message and session

### 💰 Accurate Cost Calculation
- Model-specific pricing (Sonnet 4.5, Opus 4.5, Haiku 4)
- Cache operation costs
- Per-message costs
- Session totals

### 🗂️ Session Organization
- Sessions grouped by ID
- Named with summaries
- Chronologically ordered
- Message ordering within sessions
- Original timestamps preserved

### 🔄 Real-Time Monitoring
- Detects new sessions automatically
- Updates every 2 seconds (configurable)
- Background operation support

---

## What You'll See in Phoenix

### Session Timeline
- All sessions organized chronologically
- Session names and summaries
- Project grouping
- Clickable for details

### Token Analytics
- Per-message token breakdown
- Input vs output vs cache
- Total tokens per session
- Token usage trends

### Cost Dashboard
- Per-message costs
- Session total costs
- Cost over time
- Model-specific breakdowns

### Quality Metrics
- Detected errors and hallucinations
- Confidence scores
- Quality ratings per session

### Project Analytics
- Sessions per project
- Token usage per project
- Cost per project
- Activity timeline

---

## Troubleshooting

### No sessions showing?
Check if session files exist:
```bash
ls ~/.claude/projects/
```

### Token usage missing?
✅ **FIXED!** Token data now comes from session JSONL files automatically

### Only one project showing?
- Verify `config.yaml` has `mode: "all"`
- Check other projects exist in `~/.claude/projects/`

### Port 6006 already in use?
```bash
# Linux/Mac
lsof -ti:6006 | xargs kill -9

# Windows
netstat -ano | findstr :6006
taskkill /PID <process_id> /F
```

---

## Architecture

```
Claude Code Projects
    ↓
~/.claude/projects/<project>/*.jsonl
    ↓
SessionParser (discovers & parses all projects)
    ↓
PhoenixIntegration (sends to Phoenix)
    ↓
Phoenix Dashboard (http://127.0.0.1:6006)
```

---

## Troubleshooting

### Port 6006 Already in Use
```bash
# Windows
netstat -ano | findstr :6006
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:6006 | xargs kill -9
```

### No History File Found
Make sure Claude Code is installed and you've run at least one session.
Check: `C:\Users\premr\.claude\history.jsonl`

### Module Not Found Errors
```bash
venv\Scripts\activate
pip install -r requirements.txt
```

See **TROUBLESHOOTING.md** for more help.

---

## Run in Background

### Windows
```batch
start /B python start_observatory.py
```

### Linux/Mac
```bash
nohup python start_observatory.py > observatory.log 2>&1 &
```

---

## Documentation

- **README.md**: Full feature documentation
- **QUICK_START.md**: This file - get started fast
- **CREDITS.md**: Attribution to original project
- **TROUBLESHOOTING.md**: Common problems and solutions
- **CHANGELOG.md**: Version history and changes

---

## Next Steps

1. ✅ Run: `python start_observatory.py`
2. 🌐 Open: http://localhost:6006
3. 💻 Use Claude Code normally
4. 📊 Watch your metrics in real-time!

---

**The observatory automatically monitors ALL your Claude Code projects!**

Happy monitoring! 🔭