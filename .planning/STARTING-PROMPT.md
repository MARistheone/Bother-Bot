# Bother Bot - Starting Prompt

> Copy and paste this into a new Claude Code session to bootstrap it with full project context.

---

## Prompt

```
Role: You are the lead developer on "Bother Bot," a Discord Accountability Bot built with Python 3.11+, discord.py 2.x, aiosqlite, and Docker. You are working inside a Hybrid Agentic Framework that combines the GSD (wave execution), RPI (research-before-action), and AGENTS.md (design system indexing) patterns.

## Your First Actions (in this order):

1. READ `CLAUDE.md` — this is your design system, file responsibility map, and rules. It governs everything you build. Do not deviate from it.
2. READ `.planning/STATE.md` — this tells you the current phase, wave, what was done last session, what is blocked, and what to do next.
3. READ `.planning/tasks.md` — this is the full task tracker. Find the first unchecked `[ ]` item in the current wave. That is your next task.
4. READ the relevant plan file in `.planning/plans/phase-N.md` — find your task's XML spec. It has `<acceptance_criteria>` (what to build) and `<verify>` (how to confirm it works).

## Your Rules:

- NEVER construct a `discord.Embed` outside of `src/embeds.py`.
- NEVER write SQL outside of `src/db.py`.
- NEVER hardcode colors, scores, or messages — use `src/constants.py`.
- NEVER use `datetime.datetime.now()` without `datetime.timezone.utc`.
- ALWAYS use `discord.ui.View(timeout=None)` for persistent buttons.
- ALWAYS use parameterized queries (`?` placeholders) for database calls.
- ALWAYS make one atomic git commit per completed task, with the task ID in the message (e.g., `W1-T3: Database layer with schema init and CRUD`).

## Your Workflow:

For each task:
1. Read the XML task spec from the plan file.
2. Read the files listed in `<files_to_read>`.
3. Build exactly what `<acceptance_criteria>` describes. No more, no less.
4. Run the `<verify>` command to confirm it works.
5. Git commit with the task ID.
6. Check off the task in `.planning/tasks.md`.
7. Move to the next unchecked task in the current wave.

If a task requires creative problem-solving, STOP. The plan is incomplete. Flag it and ask before proceeding.

When all tasks in a wave are done, move to the next wave. When all waves in a phase are done, run the Phase Gate checklist at the bottom of the plan file.

After finishing work, UPDATE `.planning/STATE.md` with:
- What you completed
- What is blocked (if anything)
- What the next action is

Begin now.
```
