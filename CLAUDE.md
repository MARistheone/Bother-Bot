# CLAUDE.md - Bother Bot

## Project Summary

Discord accountability bot for a small, private friend server. Tracks daily, weekly, and one-off tasks. Gamifies completion with a point system. Features automated and user-triggered "nagging" mechanics for overdue items. Runs on a Synology NAS via Docker.

## Tech Stack

- Python 3.11+ | discord.py 2.x (app_commands, discord.ui) | aiosqlite | SQLite
- discord.ext.tasks for scheduled loops (overdue checker, Wall of Shame, daily reset)
- Docker + Docker Compose on Synology NAS (Intel)

## File Responsibilities (STRICT)

| File | Responsibility | Rule |
|------|---------------|------|
| `src/bot.py` | Bot init, tree sync, cog loading | NOTHING ELSE goes here |
| `src/db.py` | ALL database operations | No SQL outside this file |
| `src/embeds.py` | ALL embed construction | Every discord.Embed is built here. Cogs NEVER construct embeds. |
| `src/views.py` | ALL discord.ui.View and Button subclasses | The interactive "click surface" |
| `src/scoring.py` | Point calculation logic | No database calls, no Discord API calls. Pure functions. |
| `src/constants.py` | Colors, scoring values, message templates | Single source of truth for all magic numbers and strings |
| `src/cogs/tasks.py` | /task command group, button interaction callbacks | Delegates to embeds.py, views.py, db.py |
| `src/cogs/accountability.py` | /opt-in, /prod, /board refresh commands | Delegates to embeds.py, db.py |
| `src/cogs/loops.py` | All discord.ext.tasks loops | Overdue checker (hourly), Wall of Shame (9PM), Daily Reset (midnight) |

## Database Patterns

- ALWAYS use `async with aiosqlite.connect(DB_PATH) as db:` -- never hold connections open
- ALWAYS use parameterized queries: `await db.execute("SELECT * FROM users WHERE discord_id = ?", (uid,))`
- DB_PATH = `/app/data/database.db` (Docker volume-mounted)
- Enable WAL mode on connection: `await db.execute("PRAGMA journal_mode=WAL")`
- Enable foreign keys: `await db.execute("PRAGMA foreign_keys = ON")`

### Schema

```sql
CREATE TABLE IF NOT EXISTS users (
    discord_id TEXT PRIMARY KEY,
    score INTEGER DEFAULT 0,
    private_channel_id TEXT
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    discord_id TEXT REFERENCES users(discord_id),
    description TEXT NOT NULL,
    status TEXT DEFAULT 'pending',  -- 'pending', 'completed', 'overdue'
    message_id TEXT,
    due_date DATETIME,
    recurrence TEXT DEFAULT 'none',  -- 'none', 'daily', 'weekly'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Discord Patterns

- Use `@app_commands.command()` for slash commands, NOT prefix commands
- Use `discord.ui.View(timeout=None)` for persistent buttons (survive bot restarts)
- Register persistent views in `bot.py` `setup_hook()`
- Use `interaction.response.edit_message()` for button clicks that modify the source message
- Use `interaction.response.send_message(ephemeral=True)` for confirmation feedback
- Sync command tree: guild-specific for development, global for production
- Channel permission overrides: use `discord.PermissionOverwrite` objects, not raw ints
- Store the accountability board's message_id in the database so it can be re-fetched after restart

## Design System (Discord "GUI")

### Color Tokens (defined in constants.py as hex integers)

| Token | Hex | Int | Usage |
|-------|-----|-----|-------|
| COLOR_BOARD | #2B2D31 | 0x2B2D31 | Accountability board embed |
| COLOR_DEFAULT_TASK | #5865F2 | 0x5865F2 | New/pending task in private channel |
| COLOR_COMPLETE | #57F287 | 0x57F287 | Completed task embed |
| COLOR_OVERDUE | #ED4245 | 0xED4245 | Overdue task embed |

### Status Emojis

| Status | Display |
|--------|---------|
| pending | :yellow_circle: [PENDING] |
| completed | :green_circle: [DONE] |
| overdue | :red_circle: [OVERDUE] |

### Scoring Constants

| Event | Points |
|-------|--------|
| Task completed | +10 |
| Overdue per day | -5 |
| Snooze used | -2 |

### Button Patterns

- Mark Done: `style=discord.ButtonStyle.success` (green), `custom_id=f"done_{task_id}"`
- Snooze: `style=discord.ButtonStyle.secondary` (grey), `custom_id=f"snooze_{task_id}"`
- On complete: edit embed to COLOR_COMPLETE, strikethrough description (`~~text~~`), remove view (no buttons)
- On overdue: edit embed to COLOR_OVERDUE, prepend "OVERDUE: " to title

### Embed Construction Rules

- EVERY embed is built via a function in `src/embeds.py`
- Return `discord.Embed` objects, not dicts
- Always set `.timestamp = datetime.datetime.now(datetime.timezone.utc)`
- Accountability board: grouped by user, sorted by score descending, bold usernames and scores

### Tone of Voice

- "Drill sergeant who is secretly your best friend"
- Playfully judgmental, slightly snarky, but encouraging
- Public messages (#the-meat-grinder): blockquote format (`> message`)
- Wall of Shame: explicitly ping users with `<@user_id>`
- Celebration messages: include party emoji, mention what was completed
- Store randomized message templates in constants.py (5+ per category)

## Channel Architecture

| Channel | Type | Purpose |
|---------|------|---------|
| #accountability-board | Public, Read-Only | Single persistent embed showing all users, tasks, scores |
| #the-meat-grinder | Public, Interactive | Celebrations, Wall of Shame, /prod responses |
| #username-tasks | Private, 1-on-1 | Per-user task inbox with interactive buttons |

## Docker Constraints

- Base image: `python:3.11-slim`
- Set `ENV TZ="America/New_York"`
- Volume mount: `./data:/app/data` (SQLite lives here)
- Token via `env_file: .env` (NEVER hardcode)
- `restart: unless-stopped`

## Do's

- DO centralize all embeds in embeds.py and all views in views.py
- DO use `timeout=None` on persistent Views and re-register them in setup_hook
- DO use WAL mode and parameterized queries for all database access
- DO keep scoring math in scoring.py with no side effects
- DO use guild-specific command sync during development (`tree.sync(guild=...)`)
- DO store the board's message_id in the database for re-fetch after restart
- DO use `datetime.timezone.utc` for all internal timestamps; convert to local only for display
- DO use atomic git commits per task with task IDs in commit messages (e.g., `W1-T3: Database layer`)

## Don'ts

- DON'T construct embeds outside of embeds.py
- DON'T put SQL outside of db.py
- DON'T use `bot.wait_for()` for button interactions -- use persistent Views
- DON'T use global variables for database connections -- open/close per operation
- DON'T hardcode channel IDs -- store them in the database or environment variables
- DON'T use `on_message` for command handling -- use app_commands exclusively
- DON'T commit .env files. Use .env.example as a template
- DON'T use `datetime.datetime.now()` without timezone -- always use `datetime.datetime.now(datetime.timezone.utc)`
- DON'T use prefix commands (! or $) -- slash commands only

## Planning System

- All plans live in `.planning/` directory
- Current state tracked in `.planning/STATE.md`
- Task tracker in `.planning/tasks.md` (flat checklist grouped by waves)
- Before starting work: read STATE.md to understand current phase/wave
- After completing work: update STATE.md with what was done and what's next
- Task specs use XML format with `<acceptance_criteria>` and `<verify>` blocks

## Slash Commands

| Command | Description |
|---------|-------------|
| `/opt-in` or `/init` | Register user, create private channel, set score to 0 |
| `/task add [description] [due_date] [recurrence]` | Add a new task |
| `/prod [user]` | Public reminder for user's overdue tasks |
| `/board refresh` | Force redraw of #accountability-board (admin) |
