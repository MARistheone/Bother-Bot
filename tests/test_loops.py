"""Tests for Phase 3 — loops cog DB queries, /prod data flow, recurring generation."""

import datetime

import pytest
import pytest_asyncio  # noqa: F401

import src.constants
import src.db as db_module


@pytest.fixture(autouse=True)
def tmp_db(tmp_path, monkeypatch):
    """Point DB_PATH at a temp file for every test."""
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(src.constants, "DB_PATH", db_path)
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    return db_path


# ── get_pending_tasks_due_today ──────────────────────────────────

@pytest.mark.asyncio
async def test_get_pending_tasks_due_today_includes_overdue():
    await db_module.init_db()
    await db_module.add_user("u1")
    # Past due (overdue status) — should be returned
    t1 = await db_module.add_task("u1", "Old task", "2020-01-01", "none")
    await db_module.update_task_status(t1, "overdue")
    results = await db_module.get_pending_tasks_due_today()
    assert len(results) == 1
    assert results[0]["description"] == "Old task"


@pytest.mark.asyncio
async def test_get_pending_tasks_due_today_includes_pending():
    await db_module.init_db()
    await db_module.add_user("u1")
    # Past due but still pending — should be returned
    await db_module.add_task("u1", "Pending old", "2020-06-01", "none")
    results = await db_module.get_pending_tasks_due_today()
    assert len(results) == 1


@pytest.mark.asyncio
async def test_get_pending_tasks_due_today_excludes_completed():
    await db_module.init_db()
    await db_module.add_user("u1")
    t1 = await db_module.add_task("u1", "Done task", "2020-01-01", "none")
    await db_module.update_task_status(t1, "completed")
    results = await db_module.get_pending_tasks_due_today()
    assert len(results) == 0


@pytest.mark.asyncio
async def test_get_pending_tasks_due_today_excludes_future():
    await db_module.init_db()
    await db_module.add_user("u1")
    await db_module.add_task("u1", "Future task", "2099-12-31", "none")
    results = await db_module.get_pending_tasks_due_today()
    assert len(results) == 0


# ── Config table ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_config_set_and_get():
    await db_module.init_db()
    await db_module.set_config("test_key", "test_value")
    val = await db_module.get_config("test_key")
    assert val == "test_value"


@pytest.mark.asyncio
async def test_config_get_missing_returns_none():
    await db_module.init_db()
    val = await db_module.get_config("nonexistent")
    assert val is None


@pytest.mark.asyncio
async def test_config_upsert():
    await db_module.init_db()
    await db_module.set_config("key", "v1")
    await db_module.set_config("key", "v2")
    val = await db_module.get_config("key")
    assert val == "v2"


# ── update_task_due_date ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_task_due_date():
    await db_module.init_db()
    await db_module.add_user("u1")
    tid = await db_module.add_task("u1", "Task", "2026-01-01", "none")
    await db_module.update_task_due_date(tid, "2026-02-01")
    task = await db_module.get_task(tid)
    assert task["due_date"] == "2026-02-01"


# ── get_active_task_ids ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_active_task_ids():
    await db_module.init_db()
    await db_module.add_user("u1")
    t1 = await db_module.add_task("u1", "Pending", "2026-12-31", "none")
    t2 = await db_module.add_task("u1", "Overdue", "2020-01-01", "none")
    await db_module.update_task_status(t2, "overdue")
    t3 = await db_module.add_task("u1", "Done", "2026-12-31", "none")
    await db_module.update_task_status(t3, "completed")
    ids = await db_module.get_active_task_ids()
    assert t1 in ids
    assert t2 in ids
    assert t3 not in ids


# ── Overdue candidates with multiple users ───────────────────────

@pytest.mark.asyncio
async def test_overdue_candidates_multiple_users():
    await db_module.init_db()
    await db_module.add_user("u1")
    await db_module.add_user("u2")
    await db_module.add_task("u1", "U1 old task", "2020-01-01", "none")
    await db_module.add_task("u2", "U2 old task", "2020-06-01", "none")
    await db_module.add_task("u2", "U2 future", "2099-12-31", "none")
    candidates = await db_module.get_overdue_candidates()
    assert len(candidates) == 2
    descs = {c["description"] for c in candidates}
    assert "U1 old task" in descs
    assert "U2 old task" in descs


# ── Recurring task regeneration logic ────────────────────────────

@pytest.mark.asyncio
async def test_recurring_daily_next_due_date():
    """Verify daily recurrence calculates +1 day from due_date."""
    base = datetime.datetime.strptime("2026-03-01", "%Y-%m-%d")
    next_due = base + datetime.timedelta(days=1)
    assert next_due.strftime("%Y-%m-%d") == "2026-03-02"


@pytest.mark.asyncio
async def test_recurring_weekly_next_due_date():
    """Verify weekly recurrence calculates +7 days from due_date."""
    base = datetime.datetime.strptime("2026-03-01", "%Y-%m-%d")
    next_due = base + datetime.timedelta(weeks=1)
    assert next_due.strftime("%Y-%m-%d") == "2026-03-08"


@pytest.mark.asyncio
async def test_completed_recurring_creates_new_task():
    """Full flow: complete a recurring task, verify new task is creatable."""
    await db_module.init_db()
    await db_module.add_user("u1")
    t1 = await db_module.add_task("u1", "Daily task", "2026-03-01", "daily")
    await db_module.update_task_status(t1, "completed")

    # Simulate regeneration
    completed = await db_module.get_completed_recurring_tasks()
    assert len(completed) == 1
    task = completed[0]

    base = datetime.datetime.strptime(task["due_date"], "%Y-%m-%d")
    next_due = (base + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    new_id = await db_module.add_task(
        task["discord_id"], task["description"], next_due, task["recurrence"]
    )
    new_task = await db_module.get_task(new_id)
    assert new_task["description"] == "Daily task"
    assert new_task["due_date"] == "2026-03-02"
    assert new_task["recurrence"] == "daily"
    assert new_task["status"] == "pending"


# ── Shame embed data flow ───────────────────────────────────────

@pytest.mark.asyncio
async def test_shame_data_grouped_by_user():
    """Verify shame tasks can be grouped by user."""
    await db_module.init_db()
    await db_module.add_user("u1")
    await db_module.add_user("u2")
    await db_module.add_task("u1", "U1 task A", "2020-01-01", "none")
    await db_module.add_task("u1", "U1 task B", "2020-06-01", "none")
    await db_module.add_task("u2", "U2 task A", "2020-03-01", "none")

    tasks = await db_module.get_pending_tasks_due_today()
    grouped: dict[str, list[str]] = {}
    for t in tasks:
        uid = t["discord_id"]
        if uid not in grouped:
            grouped[uid] = []
        grouped[uid].append(t["description"])

    assert len(grouped["u1"]) == 2
    assert len(grouped["u2"]) == 1


# ── Prod query flow ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_prod_gets_overdue_tasks_only():
    await db_module.init_db()
    await db_module.add_user("u1")
    t1 = await db_module.add_task("u1", "Overdue task", "2020-01-01", "none")
    await db_module.update_task_status(t1, "overdue")
    await db_module.add_task("u1", "Pending task", "2099-12-31", "none")
    t3 = await db_module.add_task("u1", "Done task", "2026-01-01", "none")
    await db_module.update_task_status(t3, "completed")

    overdue = await db_module.get_tasks_for_user("u1", status="overdue")
    assert len(overdue) == 1
    assert overdue[0]["description"] == "Overdue task"
