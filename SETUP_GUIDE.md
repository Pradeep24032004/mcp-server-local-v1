# Personal Life Tracker — MCP Server
## Complete Setup Guide (Zero to Phone Demo)

---

## What you will have at the end

- A Python MCP server running on your laptop
- Claude Desktop connected to it locally (no internet needed)
- Your phone (Claude.ai or ChatGPT) connected via ngrok
- Live task + health tracking you can manage by talking

---

## Files in this project

```
mcp-tracker/
├── server.py                  ← The MCP server (all 16 tools)
├── requirements.txt           ← Python dependencies  
├── claude_desktop_config.json ← Config snippet for Claude Desktop
├── Procfile                   ← For Railway/Render cloud deploy
├── SETUP_GUIDE.md             ← This file
└── data/
    └── backlog.json           ← Your task + health database (auto-created if missing)
```

---

# PART 1 — Local Setup (Mac / Linux)

## Step 1 — Check Python version

Open Terminal and run:

```bash
python3 --version
```

You need Python 3.10 or higher.
If you don't have it:
- Mac: `brew install python3` (install Homebrew first from brew.sh if needed)
- Ubuntu/Debian: `sudo apt update && sudo apt install python3 python3-pip python3-venv`

---

## Step 2 — Put the project somewhere permanent

Move the mcp-tracker folder to a permanent location. Suggested:

```bash
# Mac / Linux
mkdir -p ~/projects
mv mcp-tracker ~/projects/
cd ~/projects/mcp-tracker
```

IMPORTANT: Note the full path. You will need it in Step 5.
To get it, run: `pwd`
Example output: `/Users/yourname/projects/mcp-tracker`

---

## Step 3 — Create a virtual environment

```bash
cd ~/projects/mcp-tracker
python3 -m venv venv
```

This creates a `venv/` folder with an isolated Python environment.

---

## Step 4 — Install dependencies

```bash
# Activate the virtual environment
source venv/bin/activate

# Your prompt should now show (venv) at the start

# Install MCP
pip install "mcp[cli]" fastmcp

# Confirm install worked
python -c "from mcp.server.fastmcp import FastMCP; print('MCP installed OK')"
```

Expected output: `MCP installed OK`

---

## Step 5 — Test the server in your browser (MCP Inspector)

With venv still active, run:

```bash
mcp dev server.py
```

Expected output:
```
Starting MCP inspector...
MCP Inspector running at http://localhost:5173
```

Open http://localhost:5173 in your browser.
You will see a panel showing all 16 tools.
Click any tool, fill in parameters, click Run — it works directly against your backlog.json!

Press Ctrl+C when done testing.

---

## Step 6 — Connect Claude Desktop

### 6a — Download Claude Desktop
Go to: https://claude.ai/download
Install the Mac or Windows app.

### 6b — Find the config file

Mac:
```bash
open "~/Library/Application Support/Claude/"
```
You will see a file called `claude_desktop_config.json`
If it doesn't exist, create it.

Windows:
Press Win+R, type `%APPDATA%\Claude\` and press Enter.
Look for `claude_desktop_config.json`.

### 6c — Edit the config file

Open `claude_desktop_config.json` in any text editor (VS Code recommended).

Replace its entire contents with:

```json
{
  "mcpServers": {
    "productivity-tracker": {
      "command": "/Users/yourname/projects/mcp-tracker/venv/bin/python",
      "args": ["/Users/yourname/projects/mcp-tracker/server.py", "stdio"]
    }
  }
}
```

REPLACE `/Users/yourname/projects/mcp-tracker` with YOUR actual path from Step 2.

To get your path quickly:
```bash
cd ~/projects/mcp-tracker && pwd
```

### Windows version:
```json
{
  "mcpServers": {
    "productivity-tracker": {
      "command": "C:\\Users\\YourName\\projects\\mcp-tracker\\venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\YourName\\projects\\mcp-tracker\\server.py", "stdio"]
    }
  }
}
```

### 6d — Restart Claude Desktop completely

Quit Claude Desktop (don't just close the window — fully quit it).
Reopen Claude Desktop.

### 6e — Verify it's working

In Claude Desktop, look for a small plug icon (🔌) or hammer icon near the chat input.
Click it — you should see "productivity-tracker" listed with the 16 tools.

If you don't see it:
- Check the JSON has no typos (use jsonlint.com to validate)
- Check the paths are correct and exact
- Check the venv Python path exists: `ls ~/projects/mcp-tracker/venv/bin/python`

---

## Step 7 — Try it in Claude Desktop

Type these messages and watch it work:

```
What are my tasks for today?
```
```
What should I focus on right now?
```
```
Add a task: review the deployment checklist, high priority, due tomorrow
```
```
Mark T003 as done
```
```
I weigh 74kg now
```
```
My body fat is 18.5 percent
```
```
Show me my stats
```
```
I want to track my daily coffee intake
```
(After that last one, try: "I had 3 coffees today")

---

# PART 2 — Phone Access via ngrok

This lets you talk to your local server from your phone.
Claude.ai on your phone and ChatGPT on your phone both work this way.

---

## Step 8 — Install ngrok

### Mac:
```bash
brew install ngrok/ngrok/ngrok
```

### Or download directly:
Go to https://ngrok.com/download
Download for your OS, unzip, move to a folder in your PATH.

### Create a free account:
Go to https://dashboard.ngrok.com/signup
Sign up free — this gives you a persistent subdomain.

### Add your auth token (one-time setup):
On the ngrok dashboard, copy your authtoken, then run:
```bash
ngrok config add-authtoken YOUR_TOKEN_HERE
```

---

## Step 9 — Start the server in HTTP mode

Open a NEW Terminal window (keep it running):

```bash
cd ~/projects/mcp-tracker
source venv/bin/activate
python server.py http
```

Expected output:
```
Starting HTTP server on port 8000
Connect via: http://localhost:8000
For phone: run  ngrok http 8000  in another terminal
```

Leave this terminal running. DO NOT close it.

---

## Step 10 — Start ngrok tunnel

Open ANOTHER Terminal window (second one):

```bash
ngrok http 8000
```

Expected output:
```
Session Status   online
Account          yourname@email.com (Plan: Free)
Forwarding       https://abc123.ngrok-free.app -> http://localhost:8000

Connections      ttl  opn  rt1  rt5  p50  p90
                 0    0    0.00 0.00 0.00 0.00
```

COPY the https URL shown (like `https://abc123.ngrok-free.app`).
Leave this terminal running too.

---

## Step 11a — Connect Claude.ai on your phone

1. Open https://claude.ai in your phone browser (or the Claude app)
2. Tap the menu / profile icon
3. Go to Settings
4. Look for "Integrations" or "MCP Servers" or "Connectors"
5. Tap "Add MCP Server" or "Add Integration"
6. Paste your ngrok URL: `https://abc123.ngrok-free.app`
7. Give it a name: "My Tasks"
8. Save

Now open a new conversation and say:
```
What should I work on today?
```

---

## Step 11b — Connect ChatGPT on your phone

REQUIREMENT: You need ChatGPT Plus ($20/month) or higher.
Free ChatGPT does NOT support custom MCP connectors.

### On desktop first (easier to set up):
1. Open https://chat.openai.com
2. Click your profile picture → Settings
3. Go to "Connectors" section
4. Scroll to the bottom → click "Advanced"
5. Toggle ON "Developer mode" (read the warning, accept)
6. A new "Create" button appears at the top of Connectors
7. Click "Create" → name it "My Tasks"
8. Paste your ngrok URL in the MCP Server URL field
9. Save

### To use in a chat:
1. Start a new chat
2. Click the + icon near the message box
3. Click "More"
4. Click "Developer Mode"
5. Click "Add sources"
6. Enable "My Tasks"
7. Now type: "What are my high-priority tasks?"

### On your phone:
After setting it up on desktop, open the ChatGPT mobile app.
The connector carries over. Start a new chat, enable developer mode the same way.

---

# PART 3 — Windows Setup

Same steps as Mac but with these differences:

## Python path
Use `python` instead of `python3` if needed.

## Virtual environment activation
```cmd
venv\Scripts\activate
```
Instead of `source venv/bin/activate`

## Config file location
```
%APPDATA%\Claude\claude_desktop_config.json
```
Press Win+R, type `%APPDATA%\Claude\` to open it.

## Config JSON (Windows paths use double backslash):
```json
{
  "mcpServers": {
    "productivity-tracker": {
      "command": "C:\\Users\\YourName\\projects\\mcp-tracker\\venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\YourName\\projects\\mcp-tracker\\server.py", "stdio"]
    }
  }
}
```

---

# PART 4 — Permanent Cloud Deploy (no ngrok needed)

This makes your server always available 24/7 without running ngrok.

## Option A — Railway (easiest, free)

1. Create account at https://railway.app
2. Install Railway CLI:
   ```bash
   npm install -g @railway/cli
   ```
3. Deploy:
   ```bash
   cd ~/projects/mcp-tracker
   railway login
   railway init
   railway up
   ```
4. Railway gives you a permanent URL like `https://mcp-tracker-production.up.railway.app`
5. Use that URL in Claude.ai and ChatGPT instead of the ngrok URL

## Option B — Render (also free)

1. Create account at https://render.com
2. Connect your GitHub repo
3. New Web Service → select your repo
4. Build command: `pip install "mcp[cli]" fastmcp`
5. Start command: `python server.py http`
6. Get your permanent URL

---

# PART 5 — Demo script for LinkedIn video

## Screen setup
- Left half: VS Code with `data/backlog.json` open
- Right half: Claude Desktop or chat window

## Script (4 minutes)

### Opening (30 seconds)
Say out loud while recording:
"Most people use ChatGPT and Claude as chatbots. They answer questions. But what if your AI could actually read and modify your private data — your tasks, your health stats — right from your laptop? That's what MCP enables."

### Live demo segment 1 — Reading data (45 seconds)
Type in Claude:
- "What should I focus on today?"
- "Show me my high priority tasks"

### Live demo segment 2 — Writing data (45 seconds)
Type in Claude:
- "I just finished the gym, mark T007 done"
  (Watch backlog.json update in VS Code on the left!)
- "Add a task: review the post draft, high priority, due tomorrow"

### Live demo segment 3 — Health tracking (30 seconds)
Type in Claude:
- "My body fat dropped to 18 percent"
  (Watch health section of backlog.json update live)
- "I slept 8 hours last night"

### Live demo segment 4 — Creating new fields (30 seconds)
Type in Claude:
- "I want to start tracking my daily water intake in litres"
- "I drank 2.5 litres today"

### Closing on phone (30 seconds)
Switch to phone view:
- Open Claude.ai or ChatGPT on phone
- Ask: "What are my most important tasks right now?"
- Show the answer coming from your local data

---

# PART 6 — All 16 MCP Tools Reference

| Tool | Purpose |
|------|---------|
| `list_tasks` | List all tasks, filter by status/priority/category |
| `get_task` | Full details of one task by ID |
| `add_task` | Create new task |
| `update_task_status` | Mark todo/in_progress/done |
| `update_task` | Edit any field of a task |
| `delete_task` | Remove a task |
| `search_tasks` | Keyword search across all fields |
| `get_todays_focus` | Morning briefing: top 3 + overdue |
| `get_stats` | Full dashboard: tasks + health + profile |
| `update_health_stat` | Create or update any health metric |
| `get_health_stats` | View all health metrics |
| `update_profile_field` | Create or update any custom profile field |
| `get_profile` | View all profile fields |
| `add_custom_field_to_task` | Add custom metadata to any task |
| `search` | ChatGPT Deep Research search (returns IDs) |
| `fetch` | ChatGPT Deep Research fetch (returns record) |

---

# PART 7 — Troubleshooting

## "No tools available" in Claude Desktop
- Verify the JSON has no typos (validate at jsonlint.com)
- Verify the Python path exists: `ls /path/to/venv/bin/python`
- Fully quit Claude Desktop (not just close window) and reopen
- Check Console.app (Mac) for errors if still not working

## "ModuleNotFoundError: No module named 'mcp'"
- Make sure you're using the venv Python in the config, not system Python
- Run: `source venv/bin/activate && pip install "mcp[cli]" fastmcp`

## ngrok URL not working
- Make sure `python server.py http` is running in a terminal
- Make sure ngrok is also running in a second terminal
- Try visiting the ngrok URL in your browser — you should see a response

## ChatGPT says "Could not connect to MCP server"
- The server must be running in HTTP mode: `python server.py http`
- The ngrok tunnel must be active
- ChatGPT requires Plus/Pro plan

## ngrok URL expires (free plan)
- Free ngrok URLs change every 8 hours when you restart
- Get a static domain: https://dashboard.ngrok.com/domains (free tier allows 1 static domain)
- Or deploy to Railway/Render for permanent URL

## backlog.json gets corrupted
- The file is plain JSON — open in VS Code to inspect/fix
- Or delete it and run the server — it creates a fresh empty one automatically

---

# PART 8 — Example conversations

## Morning briefing
```
You: What should I focus on today?
Claude: [calls get_todays_focus()] → Shows top 3 priorities with any overdue

You: Give me my full stats
Claude: [calls get_stats()] → Full dashboard
```

## Managing tasks
```
You: I just finished recording the video
Claude: [calls search_tasks('video')] → finds T001
        [calls update_task_status('T001', 'done')]
        → ✅ [T001] Marked done

You: Add a task to review analytics tomorrow, medium priority
Claude: [calls add_task(...)] → ✅ Added [T009]

You: Push T002 to next week
Claude: [calls update_task('T002', due_date='2026-05-27')] → ✏️ Updated
```

## Health tracking
```
You: I weigh 73.5kg now, down from 75
Claude: [calls update_health_stat('weight_kg', '73.5', 'kg')]
        → 💪 Health updated: weight_kg = 73.5 kg

You: My body fat is 18 percent
Claude: [calls update_health_stat('fat_percentage', '18', '%')]
        → 💪 Health updated: fat_percentage = 18 %
```

## Creating new tracking fields
```
You: I want to track my daily screen time
Claude: [calls update_profile_field('daily_screen_time_hours', '0')]
        → 👤 Profile field set: daily_screen_time_hours = '0'

You: Screen time today was 6 hours
Claude: [calls update_profile_field('daily_screen_time_hours', '6')]
        → 👤 Updated: daily_screen_time_hours = '6'
```

## Custom task fields
```
You: The LinkedIn post got 8500 impressions, save that to T002
Claude: [calls add_custom_field_to_task('T002', 'linkedin_impressions', '8500')]
        → ✏️ [T002] custom field 'linkedin_impressions' = '8500'
```
