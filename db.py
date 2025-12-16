import aiosqlite

DB_NAME = "content.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business TEXT,
            file_id TEXT,
            type TEXT,
            priority INTEGER DEFAULT 1,
            used_count INTEGER DEFAULT 0,
            last_used TEXT
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business TEXT,
            time TEXT
        )
        """)
        await db.commit()
