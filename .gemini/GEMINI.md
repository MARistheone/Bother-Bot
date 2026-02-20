# Bother Bot - Antigravity Agent Instructions

All project rules, architecture, file responsibilities, and design system are defined in `AGENTS.md` at the project root. Read it first and follow it exactly.

## Project Context Files

- `AGENTS.md` -- Primary rules and design system (READ FIRST)
- `.planning/STATE.md` -- Current phase, wave, blockers, next action
- `.planning/tasks.md` -- Full task tracker (checklist grouped by waves)
- `.planning/plans/phase-N-*.md` -- XML task specs with acceptance criteria and verify blocks
- `.planning/HANDOFF.md` -- Session handoff for continuity between agents

## Workflow

This project uses the GSD (Get Stuff Done) wave execution framework. See the skills in `.agent/skills/` for automated workflow steps: bootstrap, execute-task, verify-task, handoff.
