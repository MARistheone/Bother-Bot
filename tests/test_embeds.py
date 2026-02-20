"""Tests for src/embeds.py — embed property assertions."""

import discord

from src.constants import COLOR_BOARD, COLOR_COMPLETE, COLOR_DEFAULT_TASK, COLOR_OVERDUE
from src.embeds import (
    build_board_embed,
    build_celebration_embed,
    build_shame_embed,
    build_task_embed,
)


# ── Task Embed: Pending ─────────────────────────────────────────

def test_pending_task_color():
    embed = build_task_embed("Do laundry", "pending", "2026-12-31")
    assert embed.color.value == COLOR_DEFAULT_TASK


def test_pending_task_description():
    embed = build_task_embed("Do laundry", "pending", "2026-12-31")
    assert "Do laundry" in embed.description


def test_pending_task_title():
    embed = build_task_embed("Do laundry", "pending", "2026-12-31")
    assert "[PENDING]" in embed.title


def test_pending_task_due_date_field():
    embed = build_task_embed("Do laundry", "pending", "2026-12-31")
    field_names = [f.name for f in embed.fields]
    assert "Due Date" in field_names


def test_pending_task_timestamp():
    embed = build_task_embed("Do laundry", "pending", "2026-12-31")
    assert embed.timestamp is not None


# ── Task Embed: Completed ───────────────────────────────────────

def test_completed_task_color():
    embed = build_task_embed("Do laundry", "completed", "2026-12-31")
    assert embed.color.value == COLOR_COMPLETE


def test_completed_task_strikethrough():
    embed = build_task_embed("Do laundry", "completed", "2026-12-31")
    assert "~~Do laundry~~" in embed.description


def test_completed_task_title():
    embed = build_task_embed("Do laundry", "completed", "2026-12-31")
    assert "[DONE]" in embed.title


# ── Task Embed: Overdue ─────────────────────────────────────────

def test_overdue_task_color():
    embed = build_task_embed("Do laundry", "overdue", "2026-12-31")
    assert embed.color.value == COLOR_OVERDUE


def test_overdue_task_title():
    embed = build_task_embed("Do laundry", "overdue", "2026-12-31")
    assert "OVERDUE" in embed.title


# ── Task Embed: Recurrence ──────────────────────────────────────

def test_task_no_recurrence_field():
    embed = build_task_embed("Do laundry", "pending", "2026-12-31")
    field_names = [f.name for f in embed.fields]
    assert "Recurrence" not in field_names


def test_task_with_recurrence_field():
    embed = build_task_embed("Do laundry", "pending", "2026-12-31", "daily")
    fields = {f.name: f.value for f in embed.fields}
    assert "Recurrence" in fields
    assert fields["Recurrence"] == "Daily"


def test_task_no_due_date():
    embed = build_task_embed("Do laundry", "pending", None)
    field_names = [f.name for f in embed.fields]
    assert "Due Date" not in field_names


# ── Board Embed ─────────────────────────────────────────────────

def test_board_color():
    embed = build_board_embed([])
    assert embed.color.value == COLOR_BOARD


def test_board_sorted_by_score():
    users = [
        {"name": "Alice", "score": 10, "tasks": []},
        {"name": "Bob", "score": 30, "tasks": []},
        {"name": "Carol", "score": 20, "tasks": []},
    ]
    embed = build_board_embed(users)
    # Bob (30) should be first, Carol (20) second, Alice (10) third
    assert "Bob" in embed.fields[0].name
    assert "Carol" in embed.fields[1].name
    assert "Alice" in embed.fields[2].name


def test_board_user_fields():
    users = [
        {"name": "Alice", "score": 10, "tasks": [
            {"description": "Task A", "status": "pending"},
            {"description": "Task B", "status": "completed"},
        ]},
    ]
    embed = build_board_embed(users)
    assert len(embed.fields) == 1
    assert "Alice" in embed.fields[0].name
    assert "10" in embed.fields[0].name
    assert "Task A" in embed.fields[0].value
    assert "Task B" in embed.fields[0].value


def test_board_empty_tasks():
    users = [{"name": "Alice", "score": 0, "tasks": []}]
    embed = build_board_embed(users)
    assert "No tasks" in embed.fields[0].value


def test_board_footer():
    embed = build_board_embed([])
    assert embed.footer is not None
    assert "Last updated" in embed.footer.text


# ── Celebration Embed ───────────────────────────────────────────

def test_celebration_color():
    embed = build_celebration_embed("Alice", "Do stuff")
    assert embed.color.value == COLOR_COMPLETE


def test_celebration_user_in_description():
    embed = build_celebration_embed("Alice", "Do stuff")
    assert "Alice" in embed.description


def test_celebration_task_in_description():
    embed = build_celebration_embed("Alice", "Do stuff")
    assert "Do stuff" in embed.description


def test_celebration_timestamp():
    embed = build_celebration_embed("Alice", "Do stuff")
    assert embed.timestamp is not None


# ── Shame Embed ─────────────────────────────────────────────────

def test_shame_color():
    embed = build_shame_embed("Bob", ["Task 1", "Task 2"])
    assert embed.color.value == COLOR_OVERDUE


def test_shame_user_in_description():
    embed = build_shame_embed("Bob", ["Task 1"])
    assert "Bob" in embed.description


def test_shame_tasks_in_description():
    embed = build_shame_embed("Bob", ["Task 1", "Task 2"])
    assert "Task 1" in embed.description
    assert "Task 2" in embed.description


def test_shame_timestamp():
    embed = build_shame_embed("Bob", ["Task 1"])
    assert embed.timestamp is not None
