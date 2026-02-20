---
description: Run verification for a completed task using its verify block from the plan spec
---

# Verify Task

Run the verification step for a task to confirm it meets acceptance criteria.

1. Find the task's XML spec in `.planning/plans/`
2. Extract the `<verify>` block
3. Run the verification command(s)
4. If verification passes, report success
5. If verification fails, report the error and suggest fixes

## Additional Checks

After task-specific verification, also run:
- `pytest tests/` -- ensure no regressions
- Import check: `python -c "import os; os.environ['DISCORD_TOKEN']='fake'; from src.bot import bot"`

## Gate Checks

When all tasks in a wave are done, run the Phase Gate checklist from the plan file.
