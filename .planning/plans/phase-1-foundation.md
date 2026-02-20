# Phase 1: Foundation - Plan

## Goal
Build everything that can be tested without a live Discord connection: project scaffold, database layer, scoring logic, embed builders, view classes, and the bot skeleton.

## Pre-Requisite Research
- discord.py 2.x: `discord.ui.View(timeout=None)` persists across restarts when re-registered in `setup_hook()`
- discord.py 2.x: `custom_id` on buttons must be unique and is used to match interactions after restart
- aiosqlite: WAL mode allows concurrent reads during writes; set via PRAGMA on each connection
- Docker: `python:3.11-slim` base keeps image under 200MB

---

## Wave 1 (All tasks parallel - zero dependencies)

<task id="W1-T1" wave="1" depends_on="">
  <name>Project scaffold</name>
  <files_to_create>
    Dockerfile
    docker-compose.yml
    requirements.txt
    .gitignore
    .env.example
    src/__init__.py
    src/cogs/__init__.py
    tests/__init__.py
    data/.gitkeep
  </files_to_create>
  <files_to_read>CLAUDE.md (Docker Constraints section)</files_to_read>
  <acceptance_criteria>
    - Dockerfile: python:3.11-slim base, TZ=America/New_York, pip install requirements, CMD python src/bot.py
    - docker-compose.yml: service accountability-bot, volume ./data:/app/data, env_file .env, restart unless-stopped
    - requirements.txt: discord.py>=2.3, aiosqlite>=0.19, python-dotenv>=1.0
    - .gitignore: __pycache__, .env, *.db, data/database.db, .venv/
    - .env.example: DISCORD_TOKEN=your_token_here, GUILD_ID=your_guild_id_here
    - Empty __init__.py files for src/, src/cogs/, tests/
    - data/.gitkeep to ensure the data directory exists in git
  </acceptance_criteria>
  <verify>
    docker build -t bother-bot .
    # Exits 0 (image builds successfully)
  </verify>
</task>

<task id="W1-T2" wave="1" depends_on="">
  <name>Constants module</name>
  <files_to_create>src/constants.py</files_to_create>
  <files_to_read>CLAUDE.md (Design System section)</files_to_read>
  <acceptance_criteria>
    - COLOR_BOARD = 0x2B2D31
    - COLOR_DEFAULT_TASK = 0x5865F2
    - COLOR_COMPLETE = 0x57F287
    - COLOR_OVERDUE = 0xED4245
    - SCORE_COMPLETE = 10
    - SCORE_OVERDUE_PER_DAY = -5
    - SCORE_SNOOZE = -2
    - DB_PATH = "/app/data/database.db" (with override from env var for local dev)
    - CELEBRATION_MESSAGES: list of 5+ randomized snarky celebration templates with {user} and {task} placeholders
    - SHAME_MESSAGES: list of 5+ randomized snarky shame templates with {user} and {tasks} placeholders
    - PROD_MESSAGES: list of 5+ randomized prod templates
    - STATUS_EMOJI dict mapping 'pending'/'completed'/'overdue' to emoji strings
  </acceptance_criteria>
  <verify>
    python -c "from src.constants import COLOR_DEFAULT_TASK, SCORE_COMPLETE, CELEBRATION_MESSAGES, DB_PATH; print('OK')"
    # Prints "OK" and exits 0
  </verify>
</task>

<task id="W1-T3" wave="1" depends_on="">
  <name>Database layer - schema init and CRUD operations</name>
  <files_to_create>src/db.py</files_to_create>
  <files_to_read>CLAUDE.md (Database Patterns and Schema sections)</files_to_read>
  <acceptance_criteria>
    - async def init_db(): creates users and tasks tables with IF NOT EXISTS
    - async def get_connection(): returns aiosqlite connection with WAL mode and foreign keys ON
    - async def add_user(discord_id): inserts into users table
    - async def get_user(discord_id): returns user row or None
    - async def add_task(discord_id, description, due_date, recurrence): inserts task, returns task id
    - async def get_task(task_id): returns task row or None
    - async def get_tasks_for_user(discord_id, status=None): returns list of task rows
    - async def update_task_status(task_id, status): updates status field
    - async def update_task_message_id(task_id, message_id): stores Discord message ID
    - async def update_score(discord_id, delta): adds delta to user's score
    - async def get_all_users_with_tasks(): returns all users joined with their tasks (for board)
    - async def get_overdue_candidates(): returns pending tasks where due_date < now
    - async def get_pending_tasks_due_today(): returns tasks due today still pending (for Wall of Shame)
    - async def get_completed_recurring_tasks(): returns completed tasks with recurrence != 'none'
    - async def set_user_private_channel(discord_id, channel_id): stores private channel ID
    - All functions use async with aiosqlite.connect(DB_PATH) pattern
    - All queries use parameterized ? placeholders
  </acceptance_criteria>
  <verify>
    python -c "
    import asyncio
    from src.db import init_db, add_user, get_user, add_task, get_tasks_for_user
    async def test():
        await init_db()
        await add_user('test123')
        user = await get_user('test123')
        assert user is not None
        tid = await add_task('test123', 'Test task', '2026-12-31', 'none')
        tasks = await get_tasks_for_user('test123')
        assert len(tasks) == 1
        print('OK')
    asyncio.run(test())
    "
    # Prints "OK" and exits 0
  </verify>
</task>

<task id="W1-T4" wave="1" depends_on="">
  <name>Scoring module - pure point calculation functions</name>
  <files_to_create>src/scoring.py, tests/test_scoring.py</files_to_create>
  <files_to_read>CLAUDE.md (Scoring Constants section)</files_to_read>
  <acceptance_criteria>
    - def calculate_completion_score(): returns SCORE_COMPLETE (+10)
    - def calculate_overdue_penalty(days_overdue): returns SCORE_OVERDUE_PER_DAY * days_overdue
    - def calculate_snooze_penalty(): returns SCORE_SNOOZE (-2)
    - def calculate_days_overdue(due_date, now=None): returns int days between due_date and now
    - All functions are pure (no DB calls, no Discord calls, no side effects)
    - All functions import constants from src.constants
    - tests/test_scoring.py: test each function with edge cases (0 days overdue, negative score, etc.)
  </acceptance_criteria>
  <verify>
    pytest tests/test_scoring.py -v
    # All tests pass
  </verify>
</task>

---

## Wave 2 (Depends on Wave 1 - needs constants.py and db.py)

<task id="W2-T1" wave="2" depends_on="W1-T2">
  <name>Embed builders - all 4 embed types</name>
  <files_to_create>src/embeds.py</files_to_create>
  <files_to_read>CLAUDE.md (Design System section), src/constants.py</files_to_read>
  <acceptance_criteria>
    - def build_task_embed(description, status, due_date, recurrence='none'): returns discord.Embed
      - pending: COLOR_DEFAULT_TASK, description as-is, due date in field
      - completed: COLOR_COMPLETE, ~~description~~ strikethrough, [DONE] prefix
      - overdue: COLOR_OVERDUE, "OVERDUE: " prefix, red styling
      - Always includes timestamp (UTC)
      - Shows recurrence info if not 'none'
    - def build_board_embed(users_data): returns discord.Embed
      - COLOR_BOARD
      - Users sorted by score descending
      - Each user as a field: bold name, score with trophy emoji, task list with status emojis
      - Footer with last updated timestamp
    - def build_celebration_embed(user_name, task_description): returns discord.Embed
      - COLOR_COMPLETE, random celebration message from constants
    - def build_shame_embed(user_name, overdue_tasks): returns discord.Embed
      - COLOR_OVERDUE, random shame message from constants
  </acceptance_criteria>
  <verify>
    pytest tests/test_embeds.py -v
    # All embed property assertions pass
  </verify>
</task>

<task id="W2-T2" wave="2" depends_on="W1-T2">
  <name>Persistent View classes - TaskView with Done and Snooze buttons</name>
  <files_to_create>src/views.py</files_to_create>
  <files_to_read>CLAUDE.md (Button Patterns section), src/constants.py</files_to_read>
  <acceptance_criteria>
    - class TaskView(discord.ui.View):
      - timeout=None (persistent)
      - __init__(self, task_id): stores task_id, sets up buttons
      - Mark Done button: style=success (green), custom_id=f"done_{task_id}", label="Mark Done"
      - Snooze button: style=secondary (grey), custom_id=f"snooze_{task_id}", label="Snooze (1 Day)"
      - Both buttons have callback stubs (actual logic will be wired in Phase 2)
    - View has exactly 2 children (buttons)
    - custom_id format is deterministic from task_id for restart recovery
  </acceptance_criteria>
  <verify>
    python -c "
    from src.views import TaskView
    v = TaskView(task_id=42)
    assert v.timeout is None
    assert len(v.children) == 2
    assert v.children[0].custom_id == 'done_42'
    assert v.children[1].custom_id == 'snooze_42'
    print('OK')
    "
    # Prints "OK" and exits 0
  </verify>
</task>

<task id="W2-T3" wave="2" depends_on="W2-T1">
  <name>Embed verification tests</name>
  <files_to_create>tests/test_embeds.py</files_to_create>
  <files_to_read>src/embeds.py, src/constants.py</files_to_read>
  <acceptance_criteria>
    - Test pending task embed: correct color, description present, due date field exists
    - Test completed task embed: correct color, strikethrough in description
    - Test overdue task embed: correct color, "OVERDUE" in title or description
    - Test board embed: correct color, users sorted by score descending, fields present
    - Test celebration embed: correct color, user name in content
    - Test shame embed: correct color, task list in content
    - All tests use direct discord.Embed property assertions (no mocking Discord API)
  </acceptance_criteria>
  <verify>
    pytest tests/test_embeds.py -v
    # All tests pass
  </verify>
</task>

<task id="W2-T4" wave="2" depends_on="W1-T3, W1-T4">
  <name>Database and scoring tests</name>
  <files_to_create>tests/test_db.py</files_to_create>
  <files_to_read>src/db.py, src/scoring.py</files_to_read>
  <acceptance_criteria>
    - Test init_db creates tables (check sqlite_master)
    - Test add_user + get_user round-trip
    - Test add_task + get_tasks_for_user round-trip
    - Test update_task_status changes status field
    - Test update_score adds delta correctly (positive and negative)
    - Test get_overdue_candidates returns only pending tasks past due
    - Test get_completed_recurring_tasks returns only completed + recurring
    - All tests use a temporary database (tmpdir or :memory:)
    - Tests clean up after themselves
  </acceptance_criteria>
  <verify>
    pytest tests/test_db.py -v
    # All tests pass
  </verify>
</task>

---

## Wave 3 (Depends on Wave 2 - needs embeds.py and views.py)

<task id="W3-T1" wave="3" depends_on="W2-T1, W2-T2">
  <name>Bot entry point with cog loading skeleton</name>
  <files_to_create>src/bot.py</files_to_create>
  <files_to_read>CLAUDE.md (Discord Patterns section), src/views.py</files_to_read>
  <acceptance_criteria>
    - Uses discord.Client or commands.Bot with intents (message_content, members, guilds)
    - Loads token from .env via python-dotenv
    - setup_hook(): registers persistent views (TaskView), loads cogs from src/cogs/
    - on_ready: prints bot name, syncs command tree (guild-specific if GUILD_ID set, else global)
    - Does NOT contain any command definitions (those go in cogs)
    - Does NOT contain any embed construction (those go in embeds.py)
    - Calls init_db() on startup
    - Clean structure ready for cog loading in Phase 2
  </acceptance_criteria>
  <verify>
    python -c "
    # Verify the module can be imported and bot object created (does not connect)
    import os
    os.environ['DISCORD_TOKEN'] = 'fake_token_for_import_test'
    from src.bot import bot
    print('Bot object created:', type(bot).__name__)
    "
    # Prints bot type and exits 0
  </verify>
</task>

---

## Phase 1 Gate Checklist

- [ ] `pytest tests/` -- all tests pass
- [ ] `docker build -t bother-bot .` -- exits 0
- [ ] `python -c "from src.bot import bot"` -- imports without error
- [ ] All files follow CLAUDE.md rules (no SQL outside db.py, no embeds outside embeds.py)
- [ ] Atomic git commit per task with W-T IDs in commit messages
