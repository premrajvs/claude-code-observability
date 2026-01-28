How Your Claude Monitor Works  
 Your Claude Monitor is a sophisticated real-time terminal monitoring application. Here's how it all comes together:

1. Entry Point & Initialization Flow

When you run python -m claude_monitor:

1. **main**.py:19 - Python executes this file and calls \_main()
2. cli/main.py:72 - The main() function:


    - Loads settings using Pydantic
    - Sets up logging, timezone, and environment
    - Calls _run_monitoring() to start the actual monitoring

2. Core Architecture - Three-Layer System

┌─────────────────────────────────────────┐
│ UI Layer (Rich Library) │
│ - Live Display (auto-refreshing) │
│ - DisplayController │
└─────────────────────────────────────────┘
↑ callbacks
┌─────────────────────────────────────────┐
│ Orchestration Layer │
│ - MonitoringOrchestrator (threading) │
│ - SessionMonitor (state tracking) │
└─────────────────────────────────────────┘
↑ data fetch
┌─────────────────────────────────────────┐
│ Data Layer │
│ - DataManager (caching) │
│ - analyze_usage (file reading) │
└─────────────────────────────────────────┘

3. How the UI is Created (Rich Library Magic)

cli/main.py:148-164 - The UI setup:

# Creates a Rich "Live" display context

live_display = display_controller.live_manager.create_live_display(
auto_refresh=True,
refresh_per_second=0.75 # Updates 0.75 times per second
)

# Enter alternate screen mode (fullscreen terminal UI)

enter_alternate_screen()

# Start the live display

live_display.**enter**()

display_controller.py:503-528 - The LiveDisplayManager uses Rich's Live class:

- Live is a context manager that continuously refreshes content
- refresh_per_second=0.75 means it redraws the UI every ~1.3 seconds
- auto_refresh=True enables automatic updates
- Content is rendered as Rich "renderables" (Text, Group objects with markup)

4. How Data is Updated Dynamically

Background Thread for Data Fetching

orchestrator.py:41-55 - When monitoring starts:

def start(self):
self.\_monitoring = True
self.\_monitor_thread = threading.Thread(
target=self.\_monitoring_loop,
daemon=True
)
self.\_monitor_thread.start()

orchestrator.py:121-137 - The monitoring loop runs in background:

def \_monitoring_loop(self): # Initial fetch
self.\_fetch_and_process_data()

      while self._monitoring:
          # Wait for interval (default 10 seconds)
          self._stop_event.wait(timeout=self.update_interval)

          # Fetch fresh data
          self._fetch_and_process_data()

Data Flow Pipeline

1. Data Fetch (data_manager.py:38-110):


    - Checks if cached data is valid (5-second TTL)
    - If cache expired, calls analyze_usage() to read Claude's usage files
    - Implements retry logic with exponential backoff

2. Data Analysis (analysis.py:18-100):


    - Reads JSON files from ~/.claude/projects
    - Groups usage entries into "session blocks"
    - Calculates token usage, costs, burn rates
    - Returns structured data dictionary

3. Callback Notification (orchestrator.py:173-199):


    - After fetching data, calls all registered callbacks
    - The main callback is on_data_update() in cli/main.py:175

4.  UI Update (cli/main.py:175-204):
    def on_data_update(monitoring_data): # Create new display renderable
    renderable = display_controller.create_data_display(
    data, args, token_limit
    )

        # Update the live display
        live_display.update(renderable)

5.  How UI Rendering Works

display_controller.py:198-302 - The create_data_display() method:

1. Finds Active Session - Searches for the block with isActive: true
2. Processes Data - Calculates:


    - Token usage and percentages
    - Cost predictions
    - Time remaining
    - Burn rates

3. Formats Display - Creates screen buffer with Rich markup:

# Example markup

"[header]✦ ✧ ✦ ✧[/] [header]CLAUDE CODE USAGE MONITOR[/]" 4. Creates Renderable - Converts to Rich Group object:

# session_display.py formats the screen

screen_buffer = self.session_display.format_active_session_screen(...)

# buffer_manager converts to Rich renderable

return self.buffer_manager.create_screen_renderable(screen_buffer)

display_controller.py:538-561 - The buffer manager:
def create_screen_renderable(self, screen_buffer):
text_objects = []
for line in screen_buffer: # Parse Rich markup like [header]text[/]
text_obj = Text.from_markup(line)
text_objects.append(text_obj)

      # Group creates a vertical stack
      return Group(*text_objects)

6. The Update Cycle

Here's the complete cycle that runs continuously:

┌─────────────────────────────────────────────────┐
│ Every 10 seconds (update_interval): │
│ │
│ 1. Background thread wakes up │
│ 2. DataManager.get_data() │
│ ├─ Check cache (5s TTL) │
│ └─ If expired: analyze_usage() │
│ └─ Read ~/.claude/projects/\*.json │
│ │
│ 3. Orchestrator processes data │
│ ├─ Validates data │
│ ├─ Calculates token limits │
│ └─ Triggers callbacks │
│ │
│ 4. on_data_update() callback │
│ └─ DisplayController.create_data_display() │
│ ├─ Find active session │
│ ├─ Calculate metrics │
│ ├─ Format screen buffer │
│ └─ Create Rich renderable │
│ │
│ 5. live_display.update(renderable) │
│ └─ Rich Live automatically redraws │
│ │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ Every ~1.3 seconds (refresh_per_second=0.75): │
│ │
│ Rich Live re-renders the screen │
│ (even if data hasn't changed) │
└─────────────────────────────────────────────────┘

7. Key Design Patterns

1. Observer Pattern - Callbacks notify UI of data changes
1. Separation of Concerns - UI, orchestration, and data layers are independent
1. Caching - 5-second cache prevents excessive file reads
1. Threading - Background thread keeps UI responsive
1. Rich Renderables - Declarative UI that automatically updates

1. Why It Updates Smoothly

- Dual Refresh Rates:
  - Data refreshes every 10 seconds (configurable)
  - UI refreshes every ~1.3 seconds (keeps it smooth)
- Non-blocking Updates:
  - Background thread fetches data
  - Main thread just updates display
- Caching:
  - Recent data is cached
  - No file system lag on every refresh

This architecture creates a smooth, real-time monitoring experience where data flows from Claude's usage files → processing → display, all  
 orchestrated through callbacks and threading.
