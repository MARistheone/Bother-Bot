"""Tests for src/db.py — database CRUD operations."""

import asyncio
import os
import tempfile

import pytest
import pytest_asyncio  # noqa: F401 — needed for async fixtures

import src.constants
import src.db as db_module


@pytest.fixture(autouse=True)
def tmp_db(tmp_path, monkeypatch):
    """Point DB_PATH at a temp file for every test."""
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(src.constants, "DB_PATH", db_path)
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    return db_path


# ── Schema ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_init_db_creates_tables(tmp_db):
    import aiosqlite

    await db_module.init_db()
    async with aiosqlite.connect(tmp_db) as conn:
        cursor = await conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in await cursor.fetchall()]
    assert "users" in tables
    assert "tasks" in tables


# ── Users ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_add_and_get_user():
    await db_module.init_db()
    await db_module.add_user("u123")
    user = await db_module.get_user("u123")
    assert user is not None
    assert user["discord_id"] == "u123"
    assert user["score"] == 0


@pytest.mark.asyncio
async def test_get_user_returns_none():
    await db_module.init_db()
    user = await db_module.get_user("nonexistent")
    assert user is None


@pytest.mark.asyncio
async def test_add_user_duplicate_ignored():
    await db_module.init_db()
    await db_module.add_user("u123")
    await db_module.add_user("u123")  # should not raise
    user = await db_module.get_user("u123")
    assert user is not None


# ── Tasks ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_add_and_get_task():
    await db_module.init_db()
    await db_module.add_user("u123")
    task_id = await db_module.add_task("u123", "Test task", "2026-12-31", "none")
    task = await db_module.get_task(task_id)
    assert task is not None
    assert task["description"] == "Test task"
    assert task["status"] == "pending"


@pytest.mark.asyncio
async def test_get_tasks_for_user():
    await db_module.init_db()
    await db_module.add_user("u123")
    await db_module.add_task("u123", "Task A", "2026-12-31", "none")
    await db_module.add_task("u123", "Task B", "2026-12-31", "daily")
    tasks = await db_module.get_tasks_for_user("u123")
    assert len(tasks) == 2


@pytest.mark.asyncio
async def test_get_tasks_for_user_filtered():
    await db_module.init_db()
    await db_module.add_user("u123")
    await db_module.add_task("u123", "Task A", "2026-12-31", "none")
    t2 = await db_module.add_task("u123", "Task B", "2026-12-31", "none")
    await db_module.update_task_status(t2, "completed")
    pending = await db_module.get_tasks_for_user("u123", status="pending")
    assert len(pending) == 1
    assert pending[0]["description"] == "Task A"


# ── Task Status ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_task_status():
    await db_module.init_db()
    await db_module.add_user("u123")
    task_id = await db_module.add_task("u123", "Test", "2026-12-31", "none")
    await db_module.update_task_status(task_id, "completed")
    task = await db_module.get_task(task_id)
    assert task["status"] == "completed"


@pytest.mark.asyncio
async def test_update_task_message_id():
    await db_module.init_db()
    await db_module.add_user("u123")
    task_id = await db_module.add_task("u123", "Test", "2026-12-31", "none")
    await db_module.update_task_message_id(task_id, "msg_999")
    task = await db_module.get_task(task_id)
    assert task["message_id"] == "msg_999"


# ── Score ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_score_positive():
    await db_module.init_db()
    await db_module.add_user("u123")
    await db_module.update_score("u123", 10)
    user = await db_module.get_user("u123")
    assert user["score"] == 10


@pytest.mark.asyncio
async def test_update_score_negative():
    await db_module.init_db()
    await db_module.add_user("u123")
    await db_module.update_score("u123", 20)
    await db_module.update_score("u123", -5)
    user = await db_module.get_user("u123")
    assert user["score"] == 15


@pytest.mark.asyncio
async def test_update_score_accumulates():
    await db_module.init_db()
    await db_module.add_user("u123")
    await db_module.update_score("u123", 10)
    await db_module.update_score("u123", 10)
    await db_module.update_score("u123", -5)
    user = await db_module.get_user("u123")
    assert user["score"] == 15


# ── Overdue Candidates ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_overdue_candidates():
    await db_module.init_db()
    await db_module.add_user("u123")
    # Past due date — should be returned
    await db_module.add_task("u123", "Old task", "2020-01-01", "none")
    # Future due date — should NOT be returned
    await db_module.add_task("u123", "Future task", "2099-12-31", "none")
    candidates = await db_module.get_overdue_candidates()
    assert len(candidates) == 1
    assert candidates[0]["description"] == "Old task"


@pytest.mark.asyncio
async def test_get_overdue_excludes_completed():
    await db_module.init_db()
    await db_module.add_user("u123")
    tid = await db_module.add_task("u123", "Done task", "2020-01-01", "none")
    await db_module.update_task_status(tid, "completed")
    candidates = await db_module.get_overdue_candidates()
    assert len(candidates) == 0


# ── Completed Recurring Tasks ───────────────────────────────────

@pytest.mark.asyncio
async def test_get_completed_recurring_tasks():
    await db_module.init_db()
    await db_module.add_user("u123")
    # Completed + recurring — should be returned
    t1 = await db_module.add_task("u123", "Daily task", "2026-12-31", "daily")
    await db_module.update_task_status(t1, "completed")
    # Completed + non-recurring — should NOT be returned
    t2 = await db_module.add_task("u123", "One-off", "2026-12-31", "none")
    await db_module.update_task_status(t2, "completed")
    # Pending + recurring — should NOT be returned
    await db_module.add_task("u123", "Pending daily", "2026-12-31", "daily")

    results = await db_module.get_completed_recurring_tasks()
    assert len(results) == 1
    assert results[0]["description"] == "Daily task"


# ── Private Channel ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_set_user_private_channel():
    await db_module.init_db()
    await db_module.add_user("u123")
    await db_module.set_user_private_channel("u123", "ch_456")
    user = await db_module.get_user("u123")
    assert user["private_channel_id"] == "ch_456"


# ── Board Query ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_all_users_with_tasks():
    await db_module.init_db()
    await db_module.add_user("u1")
    await db_module.add_user("u2")
    await db_module.add_task("u1", "Task A", "2026-12-31", "none")
    await db_module.add_task("u1", "Task B", "2026-12-31", "none")
    await db_module.add_task("u2", "Task C", "2026-12-31", "none")
    rows = await db_module.get_all_users_with_tasks()
    assert len(rows) == 3  # 2 tasks for u1, 1 for u2
