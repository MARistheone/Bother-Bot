---
description: Bootstrap a new work session by reading project state and finding the next task
---

# Bootstrap Session

Read the following files in order to understand the current project state:

1. Read `AGENTS.md` -- the project rules, architecture, and design system
2. Read `.planning/STATE.md` -- current phase, wave, what was done last, what's blocked
3. Read `.planning/tasks.md` -- find the first unchecked `[ ]` item in the current wave
4. Read `.planning/HANDOFF.md` -- session handoff notes from the previous agent
5. Read the relevant plan file in `.planning/plans/` -- find the XML task spec for the next task

## Output

Report:
- Current phase and wave
- Next task ID and description
- Files to read and files to create/modify
- Acceptance criteria summary
- Any blockers
