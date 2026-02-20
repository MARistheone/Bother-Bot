import asyncio
import aiosqlite

async def main():
    async with aiosqlite.connect("database.db") as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM tasks;")
        rows = await cur.fetchall()
        for r in rows:
            print(dict(r))

asyncio.run(main())
