---
description: Update planning files at the end of a work session for the next agent
---

# Session Handoff

Update all planning files to capture what was done and what's next.

## Files to Update

### 1. `.planning/STATE.md`
Update with:
- Current phase and wave status
- What was completed this session (list each task ID)
- What is blocked (if anything)
- Next action for the following session

### 2. `.planning/HANDOFF.md`
Replace the "Last Session" section using the template at the bottom of the file:
- Date, duration, agent name
- Files built or modified (one per line)
- What was NOT built
- Current position (phase, wave, next task)
- Blockers
- Decisions made this session
- Open questions
- Numbered steps for the next session

### 3. `.planning/tasks.md`
- Check off `[x]` any tasks completed this session
- Add gate status if a phase was completed

## Rules

- Be brutally concise -- HANDOFF.md is not a journal
- Include enough context for a cold-start agent to pick up seamlessly
