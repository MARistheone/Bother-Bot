"""Tests for src/scoring.py — pure function assertions."""

import datetime
from src.scoring import (
    calculate_completion_score,
    calculate_overdue_penalty,
    calculate_snooze_penalty,
    calculate_days_overdue,
)
from src.constants import SCORE_COMPLETE, SCORE_OVERDUE_PER_DAY, SCORE_SNOOZE


def test_completion_score():
    assert calculate_completion_score() == SCORE_COMPLETE
    assert calculate_completion_score() == 10


def test_overdue_penalty_zero_days():
    assert calculate_overdue_penalty(0) == 0


def test_overdue_penalty_one_day():
    assert calculate_overdue_penalty(1) == SCORE_OVERDUE_PER_DAY
    assert calculate_overdue_penalty(1) == -5


def test_overdue_penalty_multiple_days():
    assert calculate_overdue_penalty(3) == -15
    assert calculate_overdue_penalty(7) == -35


def test_snooze_penalty():
    assert calculate_snooze_penalty() == SCORE_SNOOZE
    assert calculate_snooze_penalty() == -2


def test_days_overdue_not_yet_due():
    now = datetime.datetime(2026, 6, 15, tzinfo=datetime.timezone.utc)
    due = datetime.datetime(2026, 6, 20, tzinfo=datetime.timezone.utc)
    assert calculate_days_overdue(due, now) == 0


def test_days_overdue_same_day():
    now = datetime.datetime(2026, 6, 15, 12, 0, tzinfo=datetime.timezone.utc)
    due = datetime.datetime(2026, 6, 15, 8, 0, tzinfo=datetime.timezone.utc)
    assert calculate_days_overdue(due, now) == 0


def test_days_overdue_one_day():
    now = datetime.datetime(2026, 6, 16, 12, 0, tzinfo=datetime.timezone.utc)
    due = datetime.datetime(2026, 6, 15, 12, 0, tzinfo=datetime.timezone.utc)
    assert calculate_days_overdue(due, now) == 1


def test_days_overdue_multiple_days():
    now = datetime.datetime(2026, 6, 20, tzinfo=datetime.timezone.utc)
    due = datetime.datetime(2026, 6, 15, tzinfo=datetime.timezone.utc)
    assert calculate_days_overdue(due, now) == 5


def test_days_overdue_naive_due_date():
    """Naive due_date should be treated as UTC."""
    now = datetime.datetime(2026, 6, 17, tzinfo=datetime.timezone.utc)
    due = datetime.datetime(2026, 6, 15)  # naive
    assert calculate_days_overdue(due, now) == 2


def test_days_overdue_defaults_to_utc_now():
    """When now is None, should use current UTC time (just check it doesn't crash)."""
    due = datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc)
    result = calculate_days_overdue(due)
    assert result > 0
