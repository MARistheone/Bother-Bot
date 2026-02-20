"""Database operations. ALL SQL lives here and nowhere else."""

import aiosqlite
from src.constants import DB_PATH


async def get_connection() -> aiosqlite.Connection:
    """Open a connection with WAL mode and foreign keys enabled."""
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys = ON")
    return db


async def init_db() -> None:
    """Create tables if they don't exist."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                discord_id TEXT PRIMARY KEY,
                score INTEGER DEFAULT 0,
                private_channel_id TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id TEXT REFERENCES users(discord_id),
                description TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                message_id TEXT,
                due_date DATETIME,
                recurrence TEXT DEFAULT 'none',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        await db.commit()


async def add_user(discord_id: str) -> None:
    """Insert a new user. Ignores if already exists."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (discord_id) VALUES (?)",
            (discord_id,),
        )
        await db.commit()


async def get_user(discord_id: str):
    """Return a user row or None."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM users WHERE discord_id = ?",
            (discord_id,),
        )
        return await cursor.fetchone()


async def set_user_private_channel(discord_id: str, channel_id: str) -> None:
    """Store the private channel ID for a user."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET private_channel_id = ? WHERE discord_id = ?",
            (channel_id, discord_id),
        )
        await db.commit()


async def add_task(
    discord_id: str,
    description: str,
    due_date: str,
    recurrence: str = "none",
) -> int:
    """Insert a task and return its ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO tasks (discord_id, description, due_date, recurrence) "
            "VALUES (?, ?, ?, ?)",
            (discord_id, description, due_date, recurrence),
        )
        await db.commit()
        return cursor.lastrowid


async def get_task(task_id: int):
    """Return a task row or None."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,),
        )
        return await cursor.fetchone()


async def get_tasks_for_user(discord_id: str, status: str | None = None) -> list:
    """Return all tasks for a user, optionally filtered by status."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if status:
            cursor = await db.execute(
                "SELECT * FROM tasks WHERE discord_id = ? AND status = ?",
                (discord_id, status),
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM tasks WHERE discord_id = ?",
                (discord_id,),
            )
        return await cursor.fetchall()


async def update_task_status(task_id: int, status: str) -> None:
    """Update a task's status."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE tasks SET status = ? WHERE id = ?",
            (status, task_id),
        )
        await db.commit()


async def update_task_message_id(task_id: int, message_id: str) -> None:
    """Store the Discord message ID for a task embed."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE tasks SET message_id = ? WHERE id = ?",
            (message_id, task_id),
        )
        await db.commit()


async def update_score(discord_id: str, delta: int) -> None:
    """Add delta to a user's score."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET score = score + ? WHERE discord_id = ?",
            (delta, discord_id),
        )
        await db.commit()


async def get_all_users_with_tasks() -> list:
    """Return all users joined with their tasks, for the accountability board."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT u.discord_id, u.score, t.id AS task_id, t.description,
                   t.status, t.due_date, t.recurrence
            FROM users u
            LEFT JOIN tasks t ON u.discord_id = t.discord_id
            ORDER BY u.score DESC, u.discord_id
        """)
        return await cursor.fetchall()


async def get_overdue_candidates() -> list:
    """Return pending tasks where due_date is in the past."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM tasks WHERE status = 'pending' "
            "AND due_date < datetime('now')"
        )
        return await cursor.fetchall()


async def get_pending_tasks_due_today() -> list:
    """Return tasks due today that are still pending or overdue (for Wall of Shame)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM tasks WHERE status IN ('pending', 'overdue') "
            "AND date(due_date) <= date('now')"
        )
        return await cursor.fetchall()


async def get_completed_recurring_tasks() -> list:
    """Return completed tasks that have a recurrence pattern."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM tasks WHERE status = 'completed' "
            "AND recurrence != 'none'"
        )
        return await cursor.fetchall()


async def get_config(key: str) -> str | None:
    """Return a config value or None."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT value FROM config WHERE key = ?",
            (key,),
        )
        row = await cursor.fetchone()
        return row[0] if row else None


async def set_config(key: str, value: str) -> None:
    """Insert or update a config value."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
            (key, value),
        )
        await db.commit()


async def update_task_due_date(task_id: int, new_due_date: str) -> None:
    """Update a task's due date."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE tasks SET due_date = ? WHERE id = ?",
            (new_due_date, task_id),
        )
        await db.commit()


async def update_task_details(task_id: int, description: str, due_date: str, recurrence: str) -> None:
    """Update all main details of a task."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE tasks SET description = ?, due_date = ?, recurrence = ? WHERE id = ?",
            (description, due_date, recurrence, task_id),
        )
        await db.commit()


async def get_active_task_ids() -> list[int]:
    """Return IDs of all pending/overdue tasks (for persistent view re-registration)."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id FROM tasks WHERE status IN ('pending', 'overdue')"
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]
