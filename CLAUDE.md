# CLAUDE.md - Bother Bot

> **All project rules, architecture, and design system are defined in `AGENTS.md`.**
> This file exists for Claude Code auto-loading compatibility.
> AGENTS.md is the single source of truth -- read it first, follow it exactly.

## Quick Reference

- **Rules file**: `AGENTS.md` (root) -- read this before any work
- **Current state**: `.planning/STATE.md`
- **Task tracker**: `.planning/tasks.md`
- **Task specs**: `.planning/plans/phase-N-*.md` (XML format)
- **Session handoff**: `.planning/HANDOFF.md`

## Bootstrap Sequence

1. Read `AGENTS.md` -- design system, file rules, patterns
2. Read `.planning/STATE.md` -- current phase/wave/blockers
3. Read `.planning/tasks.md` -- find next unchecked task
4. Read the relevant plan file -- find the XML spec with `<acceptance_criteria>` and `<verify>`
5. Execute the task, verify, commit, check off, move to next
