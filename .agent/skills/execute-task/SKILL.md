---
description: Execute a GSD task from its XML spec following the wave execution framework
---

# Execute Task

Given a task ID (e.g., W2-T1), execute it by following the GSD workflow:

1. Read the XML task spec from the plan file in `.planning/plans/`
2. Read all files listed in `<files_to_read>`
3. Build exactly what `<acceptance_criteria>` describes -- no more, no less
4. Follow all rules in `AGENTS.md` strictly:
   - No embeds outside `src/embeds.py`
   - No SQL outside `src/db.py`
   - No hardcoded colors/scores/messages -- use `src/constants.py`
   - All datetime uses UTC
   - Persistent views use `timeout=None`
   - Parameterized queries only
5. Run the `<verify>` command to confirm it works
6. Make one atomic git commit with the task ID in the message
7. Check off the task in `.planning/tasks.md`

## Rules

- If a task requires creative problem-solving beyond the spec, STOP and ask
- If verify fails, fix the issue before committing
- Never skip verification
