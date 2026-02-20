# Phase 3: Automation Loops - Plan

## Goal
Implement the "bother" engine — automated loops that check for overdue tasks, publicly shame procrastinators, regenerate recurring tasks, and let users prod each other. Uses `discord.ext.tasks` for scheduled loops in `src/cogs/loops.py`.

## Pre-Requisite Research
- `discord.ext.tasks.loop()` decorator for scheduled functions
- `@loop.before_loop` to wait for bot ready before starting
- `time=datetime.time(hour, minute, tzinfo=...)` for daily-at-specific-time loops
- Overdue checker: query pending tasks past due, mark overdue, edit embed, deduct score
- Wall of Shame: 9PM daily, gather all overdue/pending-due-today tasks grouped by user, post shame embed to meat grinder
- Daily Reset: midnight, find completed recurring tasks, create next occurrence, clean up
- Need to edit task embeds in users' private channels (fetch message by stored message_id)

## DB Functions Already Available
- `get_overdue_candidates()` — pending tasks past due date
- `get_pending_tasks_due_today()` — pending/overdue tasks due today or earlier
- `get_completed_recurring_tasks()` — completed tasks with recurrence != 'none'
- `update_task_status(task_id, status)`
- `update_score(discord_id, delta)`
- `get_task(task_id)`, `get_user(discord_id)`
- `add_task(discord_id, description, due_date, recurrence)` — for recurring regeneration

## Embeds Already Available
- `build_task_embed(description, status, due_date, recurrence)` — re-render as overdue
- `build_shame_embed(user_name, overdue_tasks)` — Wall of Shame

---

## Wave 1 (Parallel — all three loops in loops.py)

<task id="W1-T1" wave="1" depends_on="">
  <name>Overdue checker loop (hourly)</name>
  <files_to_create>src/cogs/loops.py</files_to_create>
  <files_to_read>AGENTS.md, src/db.py, src/embeds.py, src/scoring.py, src/constants.py, src/views.py</files_to_read>
  <acceptance_criteria>
    - Create src/cogs/loops.py as a Cog class (LoopsCog)
    - Overdue checker loop using @tasks.loop(hours=1):
      1. Call db.get_overdue_candidates() to find pending tasks past due
      2. For each task:
         a. Call db.update_task_status(task_id, "overdue")
         b. Calculate days overdue via scoring.calculate_days_overdue()
         c. Deduct points via db.update_score(discord_id, scoring.calculate_overdue_penalty(days))
         d. Re-render task embed as overdue: fetch the message in the user's private channel using stored message_id, edit with build_task_embed(..., "overdue", ...)
      3. If any tasks were marked overdue, call refresh_board()
    - Add @check_overdue.before_loop that awaits self.bot.wait_until_ready()
    - Loop starts in cog_load via self.check_overdue.start()
    - Loop cancels in cog_unload via self.check_overdue.cancel()
  </acceptance_criteria>
  <verify>
    python -c "
    import os
    os.environ['DISCORD_TOKEN'] = 'fake'
    from src.cogs.loops import LoopsCog
    print('LoopsCog imported OK')
    "
  </verify>
</task>

<task id="W1-T2" wave="1" depends_on="">
  <name>Wall of Shame loop (9PM daily)</name>
  <files_to_read>AGENTS.md, src/db.py, src/embeds.py, src/constants.py</files_to_read>
  <files_to_modify>src/cogs/loops.py</files_to_modify>
  <acceptance_criteria>
    - Wall of Shame loop using @tasks.loop(time=datetime.time(hour=21, minute=0, tzinfo=TZ)):
      1. Get meat_grinder_channel_id from config
      2. Call db.get_pending_tasks_due_today() to find pending/overdue tasks due today or earlier
      3. Group tasks by discord_id
      4. For each user with tasks:
         a. Build task list with descriptions
         b. Send shame embed via build_shame_embed(user_name, task_list) to meat grinder
         c. Include user ping (<@user_id>) in the message
      5. Silently skip if meat grinder not configured
    - Add @wall_of_shame.before_loop that awaits self.bot.wait_until_ready()
    - TZ = ZoneInfo("America/New_York") from constants or inline
  </acceptance_criteria>
  <verify>
    python -c "
    import os
    os.environ['DISCORD_TOKEN'] = 'fake'
    from src.cogs.loops import LoopsCog
    print('Wall of Shame loop exists:', hasattr(LoopsCog, 'wall_of_shame'))
    "
  </verify>
</task>

<task id="W1-T3" wave="1" depends_on="">
  <name>Daily Reset loop (midnight)</name>
  <files_to_read>AGENTS.md, src/db.py</files_to_read>
  <files_to_modify>src/cogs/loops.py</files_to_modify>
  <acceptance_criteria>
    - Daily Reset loop using @tasks.loop(time=datetime.time(hour=0, minute=0, tzinfo=TZ)):
      1. Call db.get_completed_recurring_tasks()
      2. For each completed recurring task:
         a. Calculate next due_date based on recurrence ('daily' = +1 day, 'weekly' = +7 days) from the original due_date
         b. Create a new task via db.add_task(discord_id, description, next_due_date, recurrence)
         c. Send the new task embed + TaskView to the user's private channel
         d. Store the new message_id via db.update_task_message_id()
      3. After all regeneration, refresh the board
    - Add @daily_reset.before_loop that awaits self.bot.wait_until_ready()
  </acceptance_criteria>
  <verify>
    python -c "
    import os
    os.environ['DISCORD_TOKEN'] = 'fake'
    from src.cogs.loops import LoopsCog
    print('Daily Reset loop exists:', hasattr(LoopsCog, 'daily_reset'))
    "
  </verify>
</task>

---

## Wave 2 (Depends on Wave 1)

<task id="W2-T1" wave="2" depends_on="W1-T1,W1-T2">
  <name>/prod command (public reminder for user's overdue tasks)</name>
  <files_to_modify>src/cogs/accountability.py</files_to_modify>
  <files_to_read>AGENTS.md, src/db.py, src/constants.py, src/embeds.py</files_to_read>
  <acceptance_criteria>
    - Add /prod slash command to AccountabilityCog:
      1. Takes a `user` parameter (discord.Member)
      2. Fetch overdue/pending tasks for that user via db.get_tasks_for_user(uid, status)
      3. Filter to overdue tasks only (status == 'overdue')
      4. If no overdue tasks, respond ephemeral: "They're actually on top of things... for now."
      5. Build task list string from overdue task descriptions
      6. Pick random PROD_MESSAGES template, format with {user} = mention, {tasks} = task list
      7. Send to current channel (NOT ephemeral — public shaming)
    - Import PROD_MESSAGES from constants.py
  </acceptance_criteria>
  <verify>
    python -c "
    import os
    os.environ['DISCORD_TOKEN'] = 'fake'
    from src.cogs.accountability import AccountabilityCog
    cmds = [c.name for c in AccountabilityCog.__cog_app_commands__]
    assert 'prod' in cmds, f'prod not found in {cmds}'
    print('/prod command registered OK')
    "
  </verify>
</task>

<task id="W2-T2" wave="2" depends_on="W1-T3">
  <name>Recurring task generation on completion (immediate)</name>
  <files_to_modify>src/views.py</files_to_modify>
  <files_to_read>AGENTS.md, src/db.py, src/embeds.py</files_to_read>
  <acceptance_criteria>
    - In TaskView.done_callback, after marking a recurring task complete:
      1. Check if task recurrence != 'none'
      2. If recurring, calculate next due_date ('daily' = +1 day, 'weekly' = +7 days from current due_date)
      3. Create new task via db.add_task()
      4. Build new task embed + TaskView
      5. Send to user's private channel (fetch channel from user's private_channel_id)
      6. Store new message_id via db.update_task_message_id()
      7. Register the new TaskView with bot.add_view() for persistence
    - This handles immediate regeneration; daily_reset handles the midnight sweep for any missed ones
  </acceptance_criteria>
  <verify>
    python -c "
    import os
    os.environ['DISCORD_TOKEN'] = 'fake'
    import inspect
    from src.views import TaskView
    source = inspect.getsource(TaskView.done_callback)
    assert 'recurrence' in source, 'done_callback does not reference recurrence'
    print('Recurring task generation in done_callback OK')
    "
  </verify>
</task>

---

## Phase Gate Checklist

- [ ] All three loops import cleanly (`from src.cogs.loops import LoopsCog`)
- [ ] /prod command registered in AccountabilityCog
- [ ] Recurring task regeneration triggers on Mark Done
- [ ] All existing tests still pass
- [ ] New tests for loops, /prod, and recurring generation pass
- [ ] Bot loads all cogs without errors
