# Bother Bot - Starting Prompt

> Use this to bootstrap a new session in any agentic tool (Claude Code, Antigravity, Cursor, etc.)

---

## For Claude Code

```
Read .planning/HANDOFF.md and .planning/STATE.md, then begin work.
```

Claude Code auto-loads `CLAUDE.md` (which points to `AGENTS.md`) and has the bootstrap sequence built in.

---

## For Google Antigravity

Use the **bootstrap** skill (`.agent/skills/bootstrap/`) or paste this into the Manager View:

```
Role: You are the lead developer on "Bother Bot," a Discord Accountability Bot built with Python 3.11+, discord.py 2.x, aiosqlite, and Docker. You are working inside the GSD (wave execution) framework.

## Your First Actions (in this order):

1. READ `AGENTS.md` -- this is your design system, file responsibility map, and rules. It governs everything you build. Do not deviate from it.
2. READ `.planning/STATE.md` -- this tells you the current phase, wave, what was done last session, what is blocked, and what to do next.
3. READ `.planning/tasks.md` -- this is the full task tracker. Find the first unchecked `[ ]` item in the current wave. That is your next task.
4. READ the relevant plan file in `.planning/plans/phase-N-*.md` -- find your task's XML spec. It has `<acceptance_criteria>` (what to build) and `<verify>` (how to confirm it works).

## Your Rules:

- NEVER construct a `discord.Embed` outside of `src/embeds.py`.
- NEVER write SQL outside of `src/db.py`.
- NEVER hardcode colors, scores, or messages -- use `src/constants.py`.
- NEVER use `datetime.datetime.now()` without `datetime.timezone.utc`.
- ALWAYS use `discord.ui.View(timeout=None)` for persistent buttons.
- ALWAYS use parameterized queries (`?` placeholders) for database calls.
- ALWAYS make one atomic git commit per completed task, with the task ID in the message.

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

After finishing work, UPDATE `.planning/STATE.md` and `.planning/HANDOFF.md`.

Begin now.
```

---

## For Antigravity Manager View (Multi-Agent)

To parallelize a wave, spawn one agent per task in the wave:

```
Agent 1: Execute task W1-T1 following AGENTS.md rules and the plan in .planning/plans/phase-N-*.md
Agent 2: Execute task W1-T2 following AGENTS.md rules and the plan in .planning/plans/phase-N-*.md
```

Each agent should read AGENTS.md first, then its specific task spec. After all agents complete, run the verify-task skill and then the handoff skill.
