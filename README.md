
# Personal Life Tracker — MCP Server

A local MCP (Model Context Protocol) server that connects Claude Desktop and Claude.ai on your phone to your personal task and health data. Manage your tasks, track health metrics, and create custom fields — all by talking naturally to Claude.

---

## What You Can Do

- Ask Claude: *"What should I focus on today?"* — get your top priorities
- Say: *"Mark T004 as done"* — task gets updated instantly
- Say: *"My weight is 63kg"* — health stat saved
- Say: *"Delete T009"* — task removed immediately
- Say: *"I want to track my daily water intake"* — new field created on the fly
- Works in **Claude Desktop** (Mac/Windows) and **Claude.ai on your phone**

---

## File Structure

```
productivity-tracker-app/
├── server.py                  ← MCP server with all tools
├── backlog.json               ← Your live data (tasks + health + profile)
├── requirements.txt           ← Python dependencies
├── claude_desktop_config.json ← Config reference snippet
├── Procfile                   ← For Railway/Render cloud deploy
└── venv/                      ← Python virtual environment
```

---

## All MCP Tools

| Tool | What it does |
|------|-------------|
| `list_tasks` | List all tasks, filter by status / priority / category |
| `get_task` | Full details of one task by ID |
| `add_task` | Create a new task |
| `update_task_status` | Mark a task as todo / in_progress / done |
| `update_task` | Edit any field of a task |
| `delete_task` | Permanently remove a task |
| `search_tasks` | Keyword search across all task fields |
| `get_todays_focus` | Morning briefing — top 3 priorities + overdue |
| `get_stats` | Full dashboard — tasks + health + profile |
| `update_health_stat` | Create or update any health metric |
| `get_health_stats` | View all health metrics |
| `update_profile_field` | Create or update any custom profile field |
| `get_profile` | View all profile fields |
| `add_custom_field_to_task` | Add custom metadata to any task |
| `search` | ChatGPT Deep Research — search by keyword (returns IDs) |
| `fetch` | ChatGPT Deep Research — fetch a record by ID |

---

## Requirements

- Python 3.10 or higher
- Mac or Linux (Windows instructions included below)
- Claude Desktop app (for local use)
- ngrok account (free) for phone access

---

## Part 1 — Local Setup

### Step 1 — Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/productivity-tracker-app.git
cd productivity-tracker-app
```

### Step 2 — Create virtual environment

```bash
python3 -m venv venv
```

### Step 3 — Activate and install dependencies

```bash
# Mac / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate

# Install
pip install "mcp[cli]" fastmcp
```

Verify:
```bash
python -c "from mcp.server.fastmcp import FastMCP; print('MCP installed OK')"
```

### Step 4 — Test in browser (MCP Inspector)

```bash
mcp dev server.py
```

Open **http://localhost:5173** — you'll see all 16 tools and can test them interactively.

---

## Part 2 — Connect Claude Desktop

### Step 1 — Download Claude Desktop

Download from https://claude.ai/download and install.

### Step 2 — Edit the config file

**Mac:** Open `~/Library/Application Support/Claude/claude_desktop_config.json`

```bash
open "~/Library/Application Support/Claude/"
```

**Windows:** Press `Win+R` → type `%APPDATA%\Claude\` → open `claude_desktop_config.json`

### Step 3 — Add the MCP server

Replace the file contents with:

```json
{
  "mcpServers": {
    "productivity-tracker": {
      "command": "/full/path/to/productivity-tracker-app/venv/bin/python",
      "args": ["/full/path/to/productivity-tracker-app/server.py", "stdio"]
    }
  }
}
```

Replace `/full/path/to/productivity-tracker-app` with your actual path. To get it:

```bash
cd productivity-tracker-app && pwd
```

**Windows version:**
```json
{
  "mcpServers": {
    "productivity-tracker": {
      "command": "C:\\Users\\YourName\\productivity-tracker-app\\venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\YourName\\productivity-tracker-app\\server.py", "stdio"]
    }
  }
}
```

### Step 4 — Restart Claude Desktop

Fully quit (don't just close the window) and reopen. Look for the hammer icon 🔨 near the chat input — click it to confirm the **productivity-tracker** tools are listed.

### Step 5 — Try it

```
What should I focus on today?
Add a task: review deployment checklist, high priority, due tomorrow
Mark T003 as done
My body fat is 17 percent
Show me all my health stats
Delete T001
```

---

## Part 3 — Phone Access via ngrok

This exposes your local server to the internet so Claude.ai on your phone can reach it.

### Step 1 — Install ngrok

```bash
# Mac
brew install ngrok/ngrok/ngrok

# Or download from https://ngrok.com/download
```

Create a free account at https://dashboard.ngrok.com/signup, then add your auth token:

```bash
ngrok config add-authtoken YOUR_TOKEN_HERE
```

### Step 2 — Start the HTTP server (Terminal 1)

```bash
cd productivity-tracker-app
source venv/bin/activate
python server.py http
```

Expected output:
```
Starting HTTP server on port 8000
Connect via: http://localhost:8000
For phone: run  ngrok http 8000  in another terminal
```

Keep this terminal open.

### Step 3 — Start ngrok tunnel (Terminal 2)

```bash
ngrok http 8000
```

Expected output:
```
Forwarding   https://abc123.ngrok-free.app -> http://localhost:8000
```

Copy the `https://...ngrok-free.app` URL. Keep this terminal open too.

### Step 4 — Add to Claude.ai on your phone

1. Open Claude.ai in your phone browser or app
2. Go to **Settings → Integrations** (or "MCP Servers")
3. Tap **Add MCP Server**
4. Paste your ngrok URL
5. Name it **"My Tasks"** → Save
6. Open a new conversation and ask: *"What are my tasks?"*

> Both terminals must stay running for phone access to work.

---

## Part 4 — Permanent Cloud Deploy (no ngrok needed)

Deploy to Railway for 24/7 access without running anything locally.

### Railway (easiest, free tier available)

```bash
npm install -g @railway/cli
cd productivity-tracker-app
railway login
railway init
railway up
```

Railway gives you a permanent URL like `https://your-app.up.railway.app`. Use that in Claude.ai settings instead of the ngrok URL.

The `Procfile` is already configured:
```
web: python server.py http
```

### Render (alternative)

1. Create account at https://render.com
2. Connect your GitHub repo → New Web Service
3. Build command: `pip install "mcp[cli]" fastmcp`
4. Start command: `python server.py http`
5. Use the permanent URL Render gives you

---

## Example Conversations

### Morning briefing
```
You: What should I focus on today?
Claude: [calls get_todays_focus()] → Top 3 priorities + any overdue tasks

You: Give me my full dashboard
Claude: [calls get_stats()] → Tasks summary + health stats
```

### Task management
```
You: Add a task: write the blog post, high priority, due Friday
Claude: [calls add_task(...)] → ✅ Added [T009]

You: Mark T004 as done
Claude: [calls update_task_status('T004', 'done')] → ✅ Done

You: Delete T002
Claude: [calls delete_task('T002')] → 🗑️ Deleted [T002]

You: Push T005 to next week
Claude: [calls update_task('T005', due_date='2026-05-27')] → ✏️ Updated
```

### Health tracking
```
You: I weigh 63kg now
Claude: [calls update_health_stat('weight_kg', '63', 'kg')] → 💪 Updated

You: Body fat dropped to 17 percent
Claude: [calls update_health_stat('fat_percentage', '17', '%')] → 💪 Updated

You: I slept 8 hours
Claude: [calls update_health_stat('sleep_hours', '8', 'hrs')] → 💪 Updated
```

### Creating new tracking fields
```
You: I want to track my daily coffee intake
Claude: [calls update_profile_field('daily_coffee_cups', '0')] → 👤 Field created

You: I had 3 coffees today
Claude: [calls update_profile_field('daily_coffee_cups', '3')] → 👤 Updated

You: Save that this task got 8500 LinkedIn impressions
Claude: [calls add_custom_field_to_task('T002', 'linkedin_impressions', '8500')] → ✏️ Saved
```

---

## Data File

All your data lives in `backlog.json` in the project root. It's plain JSON — you can open and edit it directly in VS Code.

Structure:
```json
{
  "meta": { "version": "2.0", "owner": "...", "last_updated": "..." },
  "profile": { "custom_fields": {} },
  "health": {},
  "tasks": [],
  "weekend_tasks": [],
  "categories": ["dev", "content", "learning", "health", "career", "personal", "weekend"],
  "stats": {}
}
```

If the file gets corrupted, delete it — the server creates a fresh empty one on next start.

---

## Troubleshooting

**"No tools available" in Claude Desktop**
- Verify the JSON in the config file has no typos — validate at jsonlint.com
- Check the venv Python path exists: `ls /path/to/venv/bin/python`
- Fully quit Claude Desktop (not just close window) and reopen

**"ModuleNotFoundError: No module named 'mcp'"**
- You're using system Python instead of venv Python in the config
- Fix: `source venv/bin/activate && pip install "mcp[cli]" fastmcp`

**"TypeError: FastMCP.run() got an unexpected keyword argument 'port'"**
- Your fastmcp version doesn't accept `port` in `run()`
- Fix in server.py: set `os.environ["PORT"] = str(port)` before calling `mcp.run(transport="streamable-http")`

**Health stats showing old data**
- Check which `backlog.json` the server is reading — it should be the root file, not `data/backlog.json`
- In server.py line 28: `DATA_FILE = os.path.join(BASE_DIR, "backlog.json")`

**ngrok URL not working on phone**
- Make sure `python server.py http` is running in Terminal 1
- Make sure `ngrok http 8000` is running in Terminal 2
- Visit the ngrok URL in your browser — you should get a JSON response

**ngrok URL changes every session (free plan)**
- Free ngrok URLs change when you restart ngrok
- Get a free static domain at https://dashboard.ngrok.com/domains
- Or deploy to Railway/Render for a permanent URL

**Claude refuses to delete tasks**
- Make sure the server instructions include the delete rule
- Fully restart Claude Desktop after any changes to server.py

---

## Windows Setup Differences

- Use `venv\Scripts\activate` instead of `source venv/bin/activate`
- Use `python` instead of `python3`
- Config file: `%APPDATA%\Claude\claude_desktop_config.json`
- Use double backslashes in JSON paths: `C:\\Users\\YourName\\...`

---

## Run Modes

| Mode | Command | Use case |
|------|---------|----------|
| stdio | Launched automatically by Claude Desktop | Claude Desktop local use |
| http | `python server.py http` | Phone access via ngrok or cloud |
| dev | `mcp dev server.py` | Browser-based tool testing |

---

## License

MIT — use it, fork it, build on it.
