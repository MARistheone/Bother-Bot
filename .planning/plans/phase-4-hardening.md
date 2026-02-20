# Phase 4: Hardening & Deploy

## Overview
Make the bot production-ready: error handling for Discord API failures, restart resilience, structured logging for Docker, and a timezone audit.

---

## Wave 1 (parallel — no interdependencies)

### W1-T1: Error Handling

<task id="W1-T1">
<title>Error handling for Discord API failures</title>
<description>
Wrap all Discord API calls (channel.send, msg.edit, interaction.response, channel.fetch_message, guild.create_text_channel) in try/except blocks catching discord.NotFound, discord.Forbidden, and discord.HTTPException. Log the error and degrade gracefully (e.g., skip embed update if message was deleted, notify user if channel creation fails).
</description>
<files_to_read>
- src/views.py
- src/cogs/accountability.py
- src/cogs/loops.py
- src/cogs/tasks.py
</files_to_read>
<files_to_modify>
- src/views.py
- src/cogs/accountability.py
- src/cogs/loops.py
- src/cogs/tasks.py
</files_to_modify>
<acceptance_criteria>
1. views.py done_callback: wrap channel.send (celebration, recurring task) and refresh_board in try/except. Log errors. Never crash on a deleted channel or missing permissions.
2. views.py snooze_callback: wrap refresh_board in try/except.
3. accountability.py refresh_board: wrap channel.fetch_message and msg.edit in try/except for NotFound (already partially done) and Forbidden/HTTPException.
4. accountability.py opt_in: wrap guild.create_text_channel in try/except for Forbidden. Send ephemeral error to user.
5. loops.py check_overdue: wrap channel.fetch_message and msg.edit (already has NotFound catch — extend to Forbidden/HTTPException).
6. loops.py wall_of_shame: wrap channel.send in try/except.
7. loops.py daily_reset: wrap channel.send in try/except.
8. tasks.py task_add: wrap channel.send in try/except for Forbidden/HTTPException.
9. All error handlers log with log.error or log.warning at appropriate severity.
10. Add a global on_command_error / tree.on_error handler in bot.py for unhandled slash command errors.
</acceptance_criteria>
<verify>
cd "c:\Users\Amiel\Documents\Bother Bot" && python -m pytest tests/ -v
</verify>
</task>

### W1-T2: Bot Restart Resilience

<task id="W1-T2">
<title>Bot restart resilience</title>
<description>
Ensure the bot recovers cleanly after a restart: re-register persistent views (already done), refresh the accountability board on startup, and handle stale channel/message IDs gracefully.
</description>
<files_to_read>
- src/bot.py
- src/cogs/accountability.py
</files_to_read>
<files_to_modify>
- src/bot.py
</files_to_modify>
<acceptance_criteria>
1. on_ready calls refresh_board(bot) to ensure the board is up-to-date after restart.
2. setup_hook logs a count of persistent views re-registered (already done).
3. If get_active_task_ids returns task IDs whose messages no longer exist, the view is still registered (discord.py handles this gracefully — just log it).
</acceptance_criteria>
<verify>
cd "c:\Users\Amiel\Documents\Bother Bot" && python -m pytest tests/ -v
</verify>
</task>

### W1-T3: Logging Setup

<task id="W1-T3">
<title>Structured logging for Docker</title>
<description>
Improve logging configuration: set discord.py's logger to WARNING to reduce noise, keep bot logger at INFO, ensure format is Docker-friendly (timestamps + level + name + message to stdout).
</description>
<files_to_read>
- src/bot.py
</files_to_read>
<files_to_modify>
- src/bot.py
</files_to_modify>
<acceptance_criteria>
1. discord.py logger set to WARNING (suppress noisy gateway/heartbeat logs).
2. Bot logger ("bother-bot") stays at INFO.
3. Log format includes ISO-like timestamp, level, logger name, and message.
4. PYTHONUNBUFFERED=1 already set in Dockerfile (verified).
5. No external logging dependencies added (stdlib only).
</acceptance_criteria>
<verify>
cd "c:\Users\Amiel\Documents\Bother Bot" && python -c "import src.bot"
</verify>
</task>

### W1-T4: Timezone Audit

<task id="W1-T4">
<title>Timezone audit</title>
<description>
Audit all datetime.now() calls across the codebase to verify they use datetime.timezone.utc. Audit SQL datetime functions (datetime('now') in SQLite is UTC). Fix any bare datetime.now() calls.
</description>
<files_to_read>
- src/embeds.py
- src/views.py
- src/cogs/loops.py
- src/cogs/tasks.py
- src/scoring.py
- src/db.py
</files_to_read>
<files_to_modify>
- (only if violations found)
</files_to_modify>
<acceptance_criteria>
1. Every datetime.now() call uses datetime.timezone.utc.
2. SQLite datetime('now') is confirmed UTC (it is by default).
3. zoneinfo usage in loops.py is correct (only for loop scheduling, not for data storage).
4. No bare datetime.now() calls exist anywhere.
</acceptance_criteria>
<verify>
cd "c:\Users\Amiel\Documents\Bother Bot" && python -c "import ast, sys; [print(f'{f}:{node.lineno}') for f in __import__('glob').glob('src/**/*.py', recursive=True) for node in ast.walk(ast.parse(open(f).read())) if isinstance(node, ast.Call) and hasattr(node, 'func') and 'now' in ast.dump(node.func) and not any('utc' in ast.dump(a) for a in node.args + node.keywords)]"
</verify>
</task>

---

## Wave 2 (depends on Wave 1)

### W2-T1: Deploy to Synology NAS

<task id="W2-T1">
<title>Deploy to Synology NAS via Docker Compose</title>
<description>
Verify Dockerfile and docker-compose.yml are production-ready. Create .env.example with all required variables. Document deployment steps.
</description>
<files_to_read>
- Dockerfile
- docker-compose.yml
- .env.example
</files_to_read>
<files_to_modify>
- docker-compose.yml (if needed)
- .env.example (if needed)
</files_to_modify>
<acceptance_criteria>
1. docker build completes without errors.
2. docker-compose up starts the bot successfully.
3. .env.example lists all required environment variables.
4. data/ directory is volume-mounted for SQLite persistence.
</acceptance_criteria>
<verify>
cd "c:\Users\Amiel\Documents\Bother Bot" && docker build -t bother-bot .
</verify>
</task>

### W2-T2: Volume Persistence Test

<task id="W2-T2">
<title>Volume persistence test</title>
<description>
Start container, create data, restart container, verify data survived.
</description>
<acceptance_criteria>
1. SQLite database persists across container restarts.
2. WAL files are in the mounted volume.
</acceptance_criteria>
<verify>
Manual: docker-compose down && docker-compose up -d && verify data in data/database.db
</verify>
</task>

### W2-T3: Final End-to-End Walkthrough

<task id="W2-T3">
<title>End-to-end walkthrough</title>
<description>
Run through the full lifecycle on a live Discord server: opt-in, add tasks, mark done, snooze, wait for overdue, see wall of shame, see daily reset.
</description>
<acceptance_criteria>
1. /opt-in creates private channel.
2. /task add creates task embed with buttons.
3. Mark Done gives green embed, celebration in meat grinder, board updates.
4. Snooze pushes due date, deducts points.
5. Overdue checker marks tasks red, deducts points.
6. Wall of Shame pings at 9PM.
7. Daily reset regenerates recurring tasks.
8. /prod calls out overdue users.
9. Bot restart: buttons still work, board intact.
</acceptance_criteria>
<verify>
Manual Discord walkthrough checklist.
</verify>
</task>

---

## Phase Gate

- [ ] All 69+ existing tests pass
- [ ] No bare datetime.now() calls
- [ ] All Discord API calls wrapped in error handling
- [ ] Bot logs cleanly to stdout (no stack traces in normal operation)
- [ ] Docker image builds and runs
- [ ] Bot survives restarts (persistent views, board re-fetch)
