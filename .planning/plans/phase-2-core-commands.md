# Phase 2: Core Commands - Plan

## Goal
Implement all slash commands and interactive button handlers that form the core task lifecycle: user registration, task creation, task completion/snooze, accountability board, and celebration messages. Requires a live Discord server with bot token.

## Pre-Requisite Research
- Private channel creation: `guild.create_text_channel()` with `overwrites` param for permissions
- PermissionOverwrite: `discord.PermissionOverwrite(read_messages=True/False)` for @everyone deny + user/bot allow
- Persistent buttons survive restart ONLY if re-registered via `bot.add_view()` in `setup_hook()`
- `interaction.response.edit_message()` for modifying the embed on button click
- `interaction.response.send_message(ephemeral=True)` for user-only confirmations
- Board needs a stored message_id in DB to re-fetch and edit after restart
- Need a config/settings table for guild-level state (board channel, board message, meat grinder channel)

## Schema Addition

A new `config` table is needed for guild-level settings:

```sql
CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

Keys: `board_channel_id`, `board_message_id`, `meat_grinder_channel_id`

New db.py functions needed:
- `async def get_config(key) -> str | None`
- `async def set_config(key, value) -> None`

---

## Wave 1 (Parallel — both cog files, plus DB additions)

<task id="W1-T1" wave="1" depends_on="">
  <name>/opt-in command + private channel creation</name>
  <files_to_create>src/cogs/accountability.py</files_to_create>
  <files_to_modify>src/db.py</files_to_modify>
  <files_to_read>CLAUDE.md (Discord Patterns, Channel Architecture), src/bot.py, src/embeds.py, src/constants.py</files_to_read>
  <acceptance_criteria>
    - Add config table to init_db() in db.py (key TEXT PRIMARY KEY, value TEXT NOT NULL)
    - Add get_config(key) and set_config(key, value) functions to db.py
    - Create src/cogs/accountability.py as a Cog class
    - /opt-in slash command:
      1. Check if user already registered (get_user). If yes, ephemeral "Already registered."
      2. Call add_user(discord_id)
      3. Create private channel: guild.create_text_channel(f"{member.display_name}-tasks", overwrites={...})
         - @everyone: PermissionOverwrite(read_messages=False)
         - member: PermissionOverwrite(read_messages=True, send_messages=True)
         - bot: PermissionOverwrite(read_messages=True, send_messages=True)
      4. Call set_user_private_channel(discord_id, channel_id)
      5. Send welcome embed to the private channel (add build_welcome_embed to embeds.py)
      6. Respond ephemeral: "You're in! Check out #{channel.name}"
    - /board refresh slash command (admin-only via @app_commands.checks.has_permissions(administrator=True)):
      1. Build board embed via build_board_embed() with data from get_all_users_with_tasks()
      2. Send new board message to the current channel
      3. Store board_channel_id and board_message_id via set_config()
      4. Respond ephemeral: "Board refreshed."
  </acceptance_criteria>
  <verify>
    python -c "
    import os
    os.environ['DISCORD_TOKEN'] = 'fake'
    import asyncio
    from src.cogs.accountability import AccountabilityCog
    from src.db import get_config, set_config
    print('AccountabilityCog imported OK')
    print('get_config, set_config imported OK')
    "
    # Prints OK and exits 0
  </verify>
</task>

<task id="W1-T2" wave="1" depends_on="">
  <name>/task add command + embed delivery to private channel</name>
  <files_to_create>src/cogs/tasks.py</files_to_create>
  <files_to_read>CLAUDE.md (Slash Commands, Button Patterns), src/embeds.py, src/views.py, src/db.py</files_to_read>
  <acceptance_criteria>
    - Create src/cogs/tasks.py as a Cog class with a "task" app_commands.Group
    - /task add [description] [due_date] [recurrence] slash command:
      1. Check user is registered (get_user). If not, ephemeral "Use /opt-in first."
      2. Call add_task(discord_id, description, due_date, recurrence)
      3. Build task embed via build_task_embed(description, 'pending', due_date, recurrence)
      4. Fetch user's private channel via user['private_channel_id']
      5. Send embed + TaskView(task_id) to private channel
      6. Store message_id via update_task_message_id(task_id, message.id)
      7. Respond ephemeral: "Task added! Check your private channel."
    - due_date parameter: string format (YYYY-MM-DD), with a sensible default (tomorrow)
    - recurrence parameter: Choice['none', 'daily', 'weekly'], default 'none'
  </acceptance_criteria>
  <verify>
    python -c "
    import os
    os.environ['DISCORD_TOKEN'] = 'fake'
    from src.cogs.tasks import TasksCog
    print('TasksCog imported OK')
    "
    # Prints OK and exits 0
  </verify>
</task>

---

## Wave 2 (Depends on Wave 1 — button handlers and board)

<task id="W2-T1" wave="2" depends_on="W1-T1, W1-T2">
  <name>Mark Done button handler</name>
  <files_to_modify>src/views.py, src/cogs/tasks.py</files_to_modify>
  <files_to_read>CLAUDE.md (Button Patterns), src/embeds.py, src/db.py, src/scoring.py</files_to_read>
  <acceptance_criteria>
    - Replace done_callback stub in views.py (or wire it from the cog) with full logic:
      1. update_task_status(task_id, 'completed')
      2. update_score(discord_id, calculate_completion_score())
      3. Edit the original message: new embed = build_task_embed(desc, 'completed', due_date, recurrence)
      4. Remove the view (set view=None on edit) so buttons disappear
      5. Respond ephemeral: "+10 points! Task completed."
    - The handler needs access to bot instance for channel fetching — pass bot reference to TaskView or use cog-based interaction handling
  </acceptance_criteria>
  <verify>
    # Manual Discord test: click Mark Done, verify embed turns green, buttons removed, score updated
    # Import test:
    python -c "
    import os
    os.environ['DISCORD_TOKEN'] = 'fake'
    from src.views import TaskView
    print('TaskView with done handler OK')
    "
  </verify>
</task>

<task id="W2-T2" wave="2" depends_on="W1-T1, W1-T2">
  <name>Snooze button handler</name>
  <files_to_modify>src/views.py, src/cogs/tasks.py, src/db.py</files_to_modify>
  <files_to_read>CLAUDE.md (Button Patterns, Scoring Constants), src/scoring.py</files_to_read>
  <acceptance_criteria>
    - Add update_task_due_date(task_id, new_due_date) to db.py
    - Replace snooze_callback stub with full logic:
      1. Get current task from DB
      2. Parse due_date, add 1 day
      3. update_task_due_date(task_id, new_due_date)
      4. update_score(discord_id, calculate_snooze_penalty())
      5. Edit the original message: new embed = build_task_embed(desc, 'pending', new_due_date, recurrence)
      6. Keep the view (buttons stay) since task is still pending
      7. Respond ephemeral: "-2 points. Snoozed until {new_date}."
  </acceptance_criteria>
  <verify>
    # Manual Discord test: click Snooze, verify due date changed, score -2, buttons remain
    python -c "
    import os
    os.environ['DISCORD_TOKEN'] = 'fake'
    from src.db import update_task_due_date
    print('update_task_due_date imported OK')
    "
  </verify>
</task>

<task id="W2-T3" wave="2" depends_on="W1-T1">
  <name>Board rendering with live data</name>
  <files_to_modify>src/cogs/accountability.py, src/embeds.py</files_to_modify>
  <files_to_read>src/db.py (get_all_users_with_tasks), src/constants.py</files_to_read>
  <acceptance_criteria>
    - Add async helper: _refresh_board(bot) that:
      1. Gets board_channel_id and board_message_id from config
      2. Fetches the channel and message objects
      3. Queries get_all_users_with_tasks() and transforms rows into the users_data format
      4. Builds embed via build_board_embed(users_data)
      5. Edits the existing board message with the new embed
      6. If message not found (deleted), sends a new one and updates config
    - This helper will be called by /board refresh and by the auto-update in W3-T2
    - Transform DB rows (flat join) into grouped users_data dicts: {name, score, tasks: [{description, status}]}
    - Use bot.get_guild() + member.display_name for user names (not raw discord_id)
  </acceptance_criteria>
  <verify>
    # Manual Discord test: /board refresh shows correct embed with all users and tasks
  </verify>
</task>

---

## Wave 3 (Depends on Wave 2 — celebrations and auto-update)

<task id="W3-T1" wave="3" depends_on="W2-T1">
  <name>Celebration message in #the-meat-grinder</name>
  <files_to_modify>src/cogs/tasks.py</files_to_modify>
  <files_to_read>src/embeds.py (build_celebration_embed), src/db.py (get_config)</files_to_read>
  <acceptance_criteria>
    - After Mark Done handler completes:
      1. Get meat_grinder_channel_id from config (if not set, skip celebration)
      2. Fetch the channel
      3. Build celebration embed via build_celebration_embed(user_name, task_description)
      4. Send embed to #the-meat-grinder
    - Need a way to set meat_grinder_channel_id — add /board setchannel or use env var
      - Simplest: add /config setchannel [channel] command to accountability cog (admin-only)
      - OR: store meat_grinder_channel_id when /board refresh is first run in a channel
    - Decision: Add /config meat-grinder [#channel] admin command to accountability cog
  </acceptance_criteria>
  <verify>
    # Manual Discord test: complete a task, verify celebration embed appears in meat grinder
  </verify>
</task>

<task id="W3-T2" wave="3" depends_on="W2-T1, W2-T3">
  <name>Board auto-update on task state change</name>
  <files_to_modify>src/cogs/tasks.py</files_to_modify>
  <files_to_read>src/cogs/accountability.py (_refresh_board helper)</files_to_read>
  <acceptance_criteria>
    - After every task state change (Mark Done, Snooze), call _refresh_board(bot)
    - If board is not yet set up (no config entries), silently skip
    - Board should reflect the new task status and updated score immediately
  </acceptance_criteria>
  <verify>
    # Manual Discord test: complete a task, verify board embed updates automatically
  </verify>
</task>

---

## Phase 2 Gate Checklist

- [ ] /opt-in creates private channel with correct permissions
- [ ] /task add delivers embed with buttons to private channel
- [ ] Mark Done: embed turns green, buttons removed, +10 score, celebration fires
- [ ] Snooze: due date shifts +1 day, -2 score, buttons remain
- [ ] /board refresh shows all users sorted by score with task statuses
- [ ] Board auto-updates after Mark Done and Snooze
- [ ] All existing tests still pass (pytest tests/)
- [ ] Bot survives restart and persistent views still work
