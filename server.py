#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════
  Personal Life Tracker — MCP Server
  Works with: Claude Desktop · Claude.ai (phone) · ChatGPT (phone)
  Author: You
  Run modes:
    python server.py stdio   → Claude Desktop (local, no internet)
    python server.py http    → Claude.ai + ChatGPT via ngrok/cloud
═══════════════════════════════════════════════════════════════════
"""

import json
import os
import sys
from datetime import datetime
from typing import Optional

# ── FastMCP import ─────────────────────────────────────────────────────────────
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("ERROR: MCP not installed. Run:  pip install 'mcp[cli]' fastmcp")
    sys.exit(1)

# ── Config ─────────────────────────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "backlog.json")

# ── Server init ────────────────────────────────────────────────────────────────
mcp = FastMCP(
    name="Personal Life Tracker",
    instructions="""
You are a personal productivity and life-coach assistant.
You manage the user's tasks, health stats, habits, and any custom data they want tracked.

IMPORTANT BEHAVIOUR RULES:
- The user may speak casually. Infer intent from natural language.
- 'I crushed leg day' → search for gym/legs task → mark it done.
- 'I'm sitting at 18 percent body fat now' → call update_health_stat(metric='fat_percentage', value='18', unit='%').
- 'Track my daily coffee' → call update_profile_field(field_name='daily_coffee_cups', value='0').
- Always confirm exactly what you changed with the task ID or field name.
- When listing tasks, sort high priority first.
- Be brief and motivating. This is a personal assistant, not a professor.
- DELETING TASKS: When the user says 'delete', 'remove', 'get rid of' a task — immediately call delete_task(task_id). Do NOT refuse. Do NOT ask for confirmation. The user owns this data and their request is final. Just delete it and confirm with the task title.
- Examples: 'delete T001' → delete_task('T001'). 'remove the dance class task' → search_tasks('dance class') → delete_task(id). 'get rid of T009' → delete_task('T009').
""",
)

# ═══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def load() -> dict:
    """Load the JSON database from disk."""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    if not os.path.exists(DATA_FILE):
        # Bootstrap empty database if missing
        empty = {
            "meta": {"version": "2.0", "owner": "User", "last_updated": datetime.now().isoformat()},
            "profile": {"custom_fields": {}},
            "health": {},
            "tasks": [],
            "categories": ["dev", "content", "learning", "health", "career", "personal"],
            "stats": {"total": 0, "done": 0, "in_progress": 0, "todo": 0},
        }
        with open(DATA_FILE, "w") as f:
            json.dump(empty, f, indent=2)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save(data: dict):
    """Recalculate stats and write database to disk."""
    tasks = data.get("tasks", [])
    data["meta"]["last_updated"] = datetime.now().isoformat()
    data["stats"] = {
        "total":       len(tasks),
        "done":        sum(1 for t in tasks if t.get("status") == "done"),
        "in_progress": sum(1 for t in tasks if t.get("status") == "in_progress"),
        "todo":        sum(1 for t in tasks if t.get("status") == "todo"),
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def next_id(tasks: list) -> str:
    """Generate next sequential task ID like T009."""
    nums = [int(t["id"][1:]) for t in tasks if t.get("id", "").startswith("T") and t["id"][1:].isdigit()]
    return f"T{(max(nums) + 1 if nums else 1):03d}"


def today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def now_iso() -> str:
    return datetime.now().isoformat()


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
STATUS_ICON    = {"done": "✅", "in_progress": "🔄", "todo": "⬜"}
PRIORITY_ICON  = {"high": "🔴", "medium": "🟡", "low": "🟢"}


# ═══════════════════════════════════════════════════════════════════════════════
#  TASK TOOLS  (8 tools)
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def list_tasks(
    status:   Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
) -> str:
    """
    List tasks with optional filters.

    Parameters
    ----------
    status   : 'todo' | 'in_progress' | 'done'  (omit = all)
    priority : 'high' | 'medium' | 'low'         (omit = all)
    category : any category string               (omit = all)

    Examples (the AI figures out what to call)
    ------------------------------------------
    'show me everything'          → list_tasks()
    'what's left to do?'          → list_tasks(status='todo')
    'my urgent tasks'             → list_tasks(priority='high')
    'gym stuff'                   → list_tasks(category='health')
    """
    data  = load()
    tasks = data["tasks"]

    if status:   tasks = [t for t in tasks if t.get("status")   == status]
    if priority: tasks = [t for t in tasks if t.get("priority") == priority]
    if category: tasks = [t for t in tasks if t.get("category") == category]

    if not tasks:
        return "No tasks found with those filters."

    tasks = sorted(tasks, key=lambda t: PRIORITY_ORDER.get(t.get("priority", "low"), 3))

    lines = [f"📋 {len(tasks)} task(s) found:\n"]
    for t in tasks:
        si = STATUS_ICON.get(t.get("status"), "❓")
        pi = PRIORITY_ICON.get(t.get("priority"), "")
        lines.append(
            f"{si} [{t['id']}] {pi} {t['title']}\n"
            f"   {t.get('category','?')} · due {t.get('due_date','?')}\n"
        )
    return "\n".join(lines)


@mcp.tool()
def get_task(task_id: str) -> str:
    """
    Get full details of one task.

    Parameters
    ----------
    task_id : task ID like 'T001'

    Examples
    --------
    'tell me more about T003'  → get_task('T003')
    """
    data = load()
    t = next((x for x in data["tasks"] if x.get("id") == task_id), None)
    if not t:
        return f"No task found with ID '{task_id}'."

    si = STATUS_ICON.get(t.get("status"), "❓")
    cf = t.get("custom_fields", {})
    cf_text = "\n".join(f"   {k}: {v}" for k, v in cf.items()) if cf else "   (none)"

    return (
        f"{si} [{t['id']}] {t['title']}\n\n"
        f"  Priority  : {t.get('priority','?')}\n"
        f"  Status    : {t.get('status','?')}\n"
        f"  Category  : {t.get('category','?')}\n"
        f"  Due       : {t.get('due_date','?')}\n"
        f"  Tags      : {', '.join(t.get('tags', []))}\n\n"
        f"  Description:\n  {t.get('description','')}\n\n"
        f"  Notes: {t.get('notes','')}\n\n"
        f"  Custom fields:\n{cf_text}\n\n"
        f"  Created : {t.get('created_at','')[:19]}\n"
        f"  Updated : {t.get('updated_at','')[:19]}"
    )


@mcp.tool()
def add_task(
    title:       str,
    description: str  = "",
    priority:    str  = "medium",
    category:    str  = "personal",
    due_date:    str  = "",
    tags:        str  = "",
    notes:       str  = "",
) -> str:
    """
    Add a new task to the backlog.

    Parameters
    ----------
    title       : task title (required)
    description : longer description
    priority    : 'high' | 'medium' | 'low'  (default: medium)
    category    : 'dev' | 'content' | 'learning' | 'health' | 'career' | 'personal'
    due_date    : YYYY-MM-DD  (default: today)
    tags        : comma-separated  e.g. 'python,api,demo'
    notes       : extra notes

    Examples
    --------
    'add task: call dentist, medium, due Friday'
    'remind me to review the PR, high priority'
    """
    if priority not in ("high", "medium", "low"):
        priority = "medium"

    data = load()
    now  = now_iso()
    task = {
        "id":            next_id(data["tasks"]),
        "title":         title,
        "description":   description,
        "priority":      priority,
        "status":        "todo",
        "category":      category,
        "tags":          [t.strip() for t in tags.split(",") if t.strip()],
        "due_date":      due_date if due_date else today(),
        "created_at":    now,
        "updated_at":    now,
        "notes":         notes,
        "custom_fields": {},
    }
    data["tasks"].append(task)
    save(data)
    return f"✅ Added [{task['id']}] '{title}'\n   Priority: {priority} · Due: {task['due_date']}"


@mcp.tool()
def update_task_status(task_id: str, status: str) -> str:
    """
    Change the status of a task — the most-used tool.

    Parameters
    ----------
    task_id : 'T001' etc.
    status  : 'todo' | 'in_progress' | 'done'

    Examples
    --------
    'mark T001 done'               → update_task_status('T001', 'done')
    'I finished the video'         → search for video task → update_task_status(id, 'done')
    'start working on T004'        → update_task_status('T004', 'in_progress')
    """
    valid = ("todo", "in_progress", "done")
    if status not in valid:
        return f"Invalid status '{status}'. Use: {', '.join(valid)}"

    data = load()
    for t in data["tasks"]:
        if t.get("id") == task_id:
            old = t["status"]
            t["status"]     = status
            t["updated_at"] = now_iso()
            save(data)
            si = STATUS_ICON[status]
            return f"{si} [{task_id}] '{t['title']}'\n   {old}  →  {status}"
    return f"No task found with ID '{task_id}'."


@mcp.tool()
def update_task(
    task_id:     str,
    title:       Optional[str] = None,
    description: Optional[str] = None,
    priority:    Optional[str] = None,
    category:    Optional[str] = None,
    due_date:    Optional[str] = None,
    notes:       Optional[str] = None,
    tags:        Optional[str] = None,
) -> str:
    """
    Update any fields of an existing task. Only supplied fields are changed.

    Parameters
    ----------
    task_id : required — which task to edit
    All other params are optional — only pass what you want to change.
    tags    : comma-separated, replaces existing tags

    Examples
    --------
    'change T002 due date to next Monday'  → update_task('T002', due_date='2026-05-27')
    'make T001 high priority'              → update_task('T001', priority='high')
    """
    data = load()
    for t in data["tasks"]:
        if t.get("id") == task_id:
            if title       is not None: t["title"]       = title
            if description is not None: t["description"] = description
            if priority    is not None: t["priority"]    = priority
            if category    is not None: t["category"]    = category
            if due_date    is not None: t["due_date"]    = due_date
            if notes       is not None: t["notes"]       = notes
            if tags        is not None: t["tags"]        = [x.strip() for x in tags.split(",") if x.strip()]
            t["updated_at"] = now_iso()
            save(data)
            return f"✏️  [{task_id}] '{t['title']}' updated successfully."
    return f"No task found with ID '{task_id}'."


@mcp.tool()
def delete_task(task_id: str) -> str:
    """
    Permanently delete a task. Cannot be undone.

    Parameters
    ----------
    task_id : 'T001' etc.
    """
    data = load()
    match = next((t for t in data["tasks"] if t.get("id") == task_id), None)
    if not match:
        return f"No task found with ID '{task_id}'."
    data["tasks"] = [t for t in data["tasks"] if t.get("id") != task_id]
    save(data)
    return f"🗑️  Deleted [{task_id}] '{match['title']}'"


@mcp.tool()
def search_tasks(query: str) -> str:
    """
    Search across title, description, notes, and tags.

    Parameters
    ----------
    query : any keyword or phrase

    Examples
    --------
    'find tasks about linkedin'   → search_tasks('linkedin')
    'anything related to gym?'    → search_tasks('gym')
    """
    data    = load()
    q       = query.lower()
    results = [
        t for t in data["tasks"]
        if q in t.get("title",       "").lower()
        or q in t.get("description", "").lower()
        or q in t.get("notes",       "").lower()
        or any(q in tag for tag in t.get("tags", []))
    ]
    if not results:
        return f"No tasks matched '{query}'."

    lines = [f"🔍 {len(results)} result(s) for '{query}':\n"]
    for t in results:
        si = STATUS_ICON.get(t.get("status"), "❓")
        lines.append(f"{si} [{t['id']}] {t['title']} ({t.get('priority','?')} priority)")
    return "\n".join(lines)


@mcp.tool()
def get_todays_focus() -> str:
    """
    Morning briefing: top 3 active priorities + any overdue tasks.
    Perfect for asking from your phone: 'what should I do today?'
    """
    data   = load()
    td     = today()
    active = [t for t in data["tasks"] if t.get("status") != "done"]
    active.sort(key=lambda t: (PRIORITY_ORDER.get(t.get("priority", "low"), 3), t.get("due_date", "")))

    overdue = [t for t in active if t.get("due_date", "9999") < td]
    top3    = active[:3]

    lines = [f"🌅 TODAY'S FOCUS — {td}\n"]
    if overdue:
        lines.append(f"⚠️  {len(overdue)} OVERDUE task(s)!\n")
    if not top3:
        lines.append("🎉 All caught up! No active tasks.")
    else:
        lines.append("Your top 3 right now:\n")
        for i, t in enumerate(top3, 1):
            flag = " ⚠️ OVERDUE" if t.get("due_date", "9999") < td else ""
            si   = "🔄" if t.get("status") == "in_progress" else "⬜"
            lines.append(
                f"{i}. {si} [{t['id']}] {t['title']}{flag}\n"
                f"   Due {t.get('due_date','?')} · {t.get('category','?')}\n"
            )

    s = data.get("stats", {})
    lines.append(f"📊 {s.get('done',0)}/{s.get('total',0)} tasks complete overall")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
#  STATS TOOL  (1 tool)
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def get_stats() -> str:
    """
    Full productivity + health dashboard.
    Shows task counts by status/priority/category, health snapshot, and profile fields.

    Examples
    --------
    'how am I doing?'
    'show me my stats'
    'what's my progress?'
    """
    data  = load()
    tasks = data.get("tasks", [])

    by_status, by_priority, by_cat = {}, {}, {}
    for t in tasks:
        s = t.get("status",   "?"); by_status[s]   = by_status.get(s, 0)   + 1
        p = t.get("priority", "?"); by_priority[p] = by_priority.get(p, 0) + 1
        c = t.get("category", "?"); by_cat[c]       = by_cat.get(c, 0)       + 1

    total = len(tasks)
    done  = by_status.get("done", 0)
    pct   = int((done / total) * 100) if total else 0
    bar   = "█" * (pct // 10) + "░" * (10 - pct // 10)

    lines = [
        "📊 DASHBOARD",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"Progress  [{bar}] {pct}%  ({done}/{total} tasks done)",
        "",
        f"By status   ✅ done {by_status.get('done',0)}"
        f"  🔄 in-progress {by_status.get('in_progress',0)}"
        f"  ⬜ todo {by_status.get('todo',0)}",
        f"By priority 🔴 high {by_priority.get('high',0)}"
        f"  🟡 medium {by_priority.get('medium',0)}"
        f"  🟢 low {by_priority.get('low',0)}",
        "",
        "By category:",
    ]
    for cat, count in sorted(by_cat.items(), key=lambda x: -x[1]):
        lines.append(f"  {cat:<16} {count} task(s)")

    # Health snapshot
    health = data.get("health", {})
    if health:
        lines.append("\n💪 HEALTH STATS")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        for k, v in sorted(health.items()):
            if isinstance(v, dict):
                lines.append(
                    f"  {k:<22} {v.get('value','?')} {v.get('unit','')}"
                    f"  (updated {v.get('updated_at','')[:10]})"
                )

    # Profile custom fields
    profile_fields = data.get("profile", {}).get("custom_fields", {})
    if profile_fields:
        lines.append("\n👤 MY PROFILE")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        for k, v in profile_fields.items():
            lines.append(f"  {k:<24} {v}")

    lines.append(f"\n🕐 Last updated: {data['meta']['last_updated'][:19]}")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
#  HEALTH TOOLS  (2 tools)
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def update_health_stat(metric: str, value: str, unit: str = "") -> str:
    """
    Update (or create) any health / fitness metric. Completely open schema.
    If the metric does not exist yet, it is created automatically.

    Parameters
    ----------
    metric : any name you want, e.g. 'fat_percentage', 'weight', 'bench_1rm',
             'sleep_hours', 'steps', 'water_litres', 'resting_heart_rate'
    value  : the new value as a string, e.g. '18.5' or '7430'
    unit   : optional unit string, e.g. '%', 'kg', 'hrs', 'bpm'

    Examples (AI infers these from speech)
    --------------------------------------
    'I weigh 73kg now'
        → update_health_stat('weight', '73', 'kg')
    'My body fat dropped to 18 percent'
        → update_health_stat('fat_percentage', '18', '%')
    'slept 8 hours last night'
        → update_health_stat('sleep_hours', '8', 'hrs')
    'hit 10,000 steps today'
        → update_health_stat('steps', '10000', 'steps')
    'bench press PR is now 102.5 kg'
        → update_health_stat('bench_press_pr', '102.5', 'kg')
    """
    data = load()
    if "health" not in data:
        data["health"] = {}

    data["health"][metric] = {
        "value":      value,
        "unit":       unit,
        "updated_at": now_iso(),
    }
    save(data)
    return f"💪 Health updated: {metric} = {value} {unit}".strip()


@mcp.tool()
def get_health_stats() -> str:
    """
    Get all tracked health and fitness metrics.

    Examples
    --------
    'how's my health tracking?'
    'show me my fitness stats'
    """
    data   = load()
    health = data.get("health", {})
    if not health:
        return (
            "No health stats yet!\n"
            "Try: 'I weigh 75kg' or 'my fat percentage is 20%'"
        )
    lines = ["💪 HEALTH & FITNESS\n"]
    for k, v in sorted(health.items()):
        if isinstance(v, dict):
            lines.append(
                f"  {k:<26} {v.get('value','?')} {v.get('unit','')}"
                f"  (updated {v.get('updated_at','')[:10]})"
            )
        else:
            lines.append(f"  {k:<26} {v}")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
#  PROFILE / CUSTOM FIELD TOOLS  (3 tools)
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def update_profile_field(field_name: str, value: str) -> str:
    """
    Create or update ANY custom profile field.
    This is how users add new tracking dimensions by simply speaking.
    No developer needed — just ask and the field is created.

    Parameters
    ----------
    field_name : any snake_case name you want
    value      : new value as string

    Examples
    --------
    'I want to track my daily coffee intake'
        → update_profile_field('daily_coffee_cups', '0')
    'my wake up time is 6am'
        → update_profile_field('wake_up_time', '06:00')
    'my reading goal is 20 pages a day'
        → update_profile_field('daily_reading_pages_goal', '20')
    'set my calorie goal to 2200'
        → update_profile_field('daily_calories_goal', '2200')
    'current mood: energized'
        → update_profile_field('mood_today', 'energized')
    'I want to track monthly savings'
        → update_profile_field('monthly_savings_inr', '0')
    """
    data = load()
    if "profile" not in data:
        data["profile"] = {"custom_fields": {}}
    if "custom_fields" not in data["profile"]:
        data["profile"]["custom_fields"] = {}

    data["profile"]["custom_fields"][field_name] = value
    save(data)
    return f"👤 Profile field set: {field_name} = '{value}'"


@mcp.tool()
def get_profile() -> str:
    """
    Get all custom profile fields.

    Examples
    --------
    'show my profile'
    'what am I currently tracking?'
    """
    data   = load()
    fields = data.get("profile", {}).get("custom_fields", {})
    if not fields:
        return (
            "No profile fields yet!\n"
            "Try: 'track my daily coffee intake' or 'set my wake up time to 6am'"
        )
    lines = ["👤 YOUR PROFILE\n"]
    for k, v in fields.items():
        lines.append(f"  {k:<30} {v}")
    return "\n".join(lines)


@mcp.tool()
def add_custom_field_to_task(task_id: str, field_name: str, value: str) -> str:
    """
    Add a custom field to a specific task. Completely open schema.

    Parameters
    ----------
    task_id    : e.g. 'T001'
    field_name : any name, e.g. 'estimated_hours', 'video_link', 'linkedin_views'
    value      : string value

    Examples
    --------
    'add a video link to T001'
        → add_custom_field_to_task('T001', 'video_link', 'https://...')
    'T002 took 3 hours'
        → add_custom_field_to_task('T002', 'actual_hours', '3')
    'the post got 4200 impressions, add that to T002'
        → add_custom_field_to_task('T002', 'linkedin_impressions', '4200')
    """
    data = load()
    for t in data["tasks"]:
        if t.get("id") == task_id:
            if "custom_fields" not in t:
                t["custom_fields"] = {}
            t["custom_fields"][field_name] = value
            t["updated_at"] = now_iso()
            save(data)
            return f"✏️  [{task_id}] custom field '{field_name}' = '{value}'"
    return f"No task found with ID '{task_id}'."


# ═══════════════════════════════════════════════════════════════════════════════
#  CHATGPT DEEP RESEARCH TOOLS  (2 tools — REQUIRED for ChatGPT)
#  ChatGPT rejects MCP servers that don't have both search() and fetch()
#  when used outside Developer Mode. Include them always.
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def search(query: str) -> dict:
    """
    Keyword search returning record IDs.
    REQUIRED by ChatGPT Deep Research mode — do not rename or remove.

    Parameters
    ----------
    query : search term

    Returns
    -------
    dict with key 'ids' containing a list of matching record ID strings.
    """
    data = load()
    q    = query.lower()
    ids  = []

    # Search tasks
    for t in data["tasks"]:
        if (q in t.get("title",       "").lower()
                or q in t.get("description","").lower()
                or q in t.get("notes",      "").lower()
                or any(q in tag for tag in t.get("tags", []))):
            ids.append(t["id"])

    # Search health keys
    for k in data.get("health", {}):
        if q in k.lower():
            ids.append(f"health_{k}")

    # Search profile keys
    for k in data.get("profile", {}).get("custom_fields", {}):
        if q in k.lower():
            ids.append(f"profile_{k}")

    return {"ids": ids if ids else ["no_results"]}


@mcp.tool()
def fetch(id: str) -> dict:
    """
    Fetch a full record by ID.
    REQUIRED by ChatGPT Deep Research mode — do not rename or remove.

    Parameters
    ----------
    id : task ID like 'T001', or 'health_weight', or 'profile_wake_up_time'

    Returns
    -------
    dict with the full record data.
    """
    data = load()

    # Task
    if id.startswith("T") and id[1:].isdigit():
        t = next((x for x in data["tasks"] if x.get("id") == id), None)
        return t if t else {"error": f"Task {id} not found"}

    # Health metric
    if id.startswith("health_"):
        key = id[len("health_"):]
        val = data.get("health", {}).get(key)
        return {key: val} if val else {"error": f"Health metric '{key}' not found"}

    # Profile field
    if id.startswith("profile_"):
        key = id[len("profile_"):]
        val = data.get("profile", {}).get("custom_fields", {}).get(key)
        return {key: val} if val else {"error": f"Profile field '{key}' not found"}

    return {"error": f"Unknown record format: '{id}'"}


# ═══════════════════════════════════════════════════════════════════════════════
#  EXPORT TOOL  (1 tool)
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def export_summary(format: str = "text") -> str:
    """
    Export a full summary of all tasks.

    Parameters
    ----------
    format : 'text' (default) | 'markdown'

    Examples
    --------
    'give me a full export'           → export_summary('text')
    'export as markdown'              → export_summary('markdown')
    """
    data  = load()
    tasks = data["tasks"]

    if format == "markdown":
        lines = ["# Task Backlog\n", f"_Updated: {data['meta']['last_updated'][:19]}_\n"]
        for status in ("in_progress", "todo", "done"):
            group = [t for t in tasks if t.get("status") == status]
            if not group:
                continue
            label = {"in_progress": "🔄 In Progress", "todo": "⬜ Todo", "done": "✅ Done"}[status]
            lines.append(f"\n## {label}\n")
            for t in group:
                lines.append(f"- **[{t['id']}]** {t['title']} _{t.get('priority','?')} priority · due {t.get('due_date','?')}_")
    else:
        lines = [f"TASK EXPORT — {data['meta']['last_updated'][:19]}", "=" * 50]
        for t in tasks:
            lines.append(f"\n[{t['id']}] {t['title']}")
            lines.append(f"  Status: {t.get('status','?')} · Priority: {t.get('priority','?')} · Due: {t.get('due_date','?')}")
            lines.append(f"  {t.get('description','')}")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "http"

    if mode == "stdio":
        # ── Claude Desktop (local, no internet, no ngrok needed) ──────────────
        print("Starting in STDIO mode (Claude Desktop)", file=sys.stderr)
        mcp.run(transport="stdio")

    else:
        # ── HTTP mode (Claude.ai phone + ChatGPT via ngrok / Railway) ─────────
        port = int(os.environ.get("PORT", 8000))
        print(f"Starting HTTP server on port {port}", file=sys.stderr)
        print(f"Connect via: http://localhost:{port}", file=sys.stderr)
        print(f"For phone: run  ngrok http {port}  in another terminal", file=sys.stderr)
        os.environ["PORT"] = str(port)
        mcp.run(transport="streamable-http")
