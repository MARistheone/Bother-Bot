"""Pure scoring functions. No DB calls, no Discord API, no side effects."""

import datetime
from src.constants import SCORE_COMPLETE, SCORE_OVERDUE_PER_DAY, SCORE_SNOOZE


def calculate_completion_score() -> int:
    """Points awarded for completing a task."""
    return SCORE_COMPLETE


def calculate_overdue_penalty(days_overdue: int) -> int:
    """Points deducted per day a task is overdue."""
    return SCORE_OVERDUE_PER_DAY * days_overdue


def calculate_snooze_penalty() -> int:
    """Points deducted for snoozing a task."""
    return SCORE_SNOOZE


def calculate_days_overdue(
    due_date: datetime.datetime,
    now: datetime.datetime | None = None,
) -> int:
    """Return the number of whole days a task is overdue (0 if not overdue)."""
    if now is None:
        now = datetime.datetime.now(datetime.timezone.utc)
    if due_date.tzinfo is None:
        due_date = due_date.replace(tzinfo=datetime.timezone.utc)
    delta = now - due_date
    return max(0, delta.days)
