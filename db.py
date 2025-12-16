import aiosqlite

DB_NAME = "content.db"


async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:

        # 🗂 Контент
        await db.execute("""
        CREATE TABLE IF NOT EXISTS content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business TEXT NOT NULL,              -- ustritso / mythai
            file_id TEXT NOT NULL,               -- Telegram file_id
            type TEXT DEFAULT 'generic',         -- atmosphere / promo / menu
            priority INTEGER DEFAULT 1,           -- 1-5
            used_count INTEGER DEFAULT 0,
            last_used TEXT
        )
        """)

        # ⏰ Расписание (время публикации)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business TEXT NOT NULL,
            time TEXT NOT NULL                  -- HH:MM
        )
        """)

        # 📊 Логи публикаций
        await db.execute("""
        CREATE TABLE IF NOT EXISTS publish_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business TEXT NOT NULL,
            content_id INTEGER,
            published_at TEXT NOT NULL,
            FOREIGN KEY (content_id) REFERENCES content(id)
        )
        """)

        await db.commit()


# 🔹 Получить весь контент бизнеса
async def get_content(business: str):
    async with aiosqlite.connect(DB_NAME) as db:
        return await db.execute_fetchall(
            "SELECT * FROM content WHERE business=?",
            (business,)
        )


# 🔹 Добавить контент
async def add_content(
    business: str,
    file_id: str,
    content_type: str = "generic",
    priority: int = 1
):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT INTO content (business, file_id, type, priority)
            VALUES (?, ?, ?, ?)
            """,
            (business, file_id, content_type, priority)
        )
        await db.commit()


# 🔹 Обновить использование контента
async def mark_used(content_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            UPDATE content
            SET used_count = used_count + 1,
                last_used = datetime('now')
            WHERE id = ?
            """,
            (content_id,)
        )
        await db.commit()


# 🔹 Лог публикации
async def log_publish(business: str, content_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT INTO publish_log (business, content_id, published_at)
            VALUES (?, ?, datetime('now'))
            """,
            (business, content_id)
        )
        await db.commit()


# 🔹 Получить расписание
async def get_schedule():
    async with aiosqlite.connect(DB_NAME) as db:
        return await db.execute_fetchall(
            "SELECT business, time FROM schedule"
        )


# 🔹 Добавить время в расписание
async def add_schedule(business: str, time: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO schedule (business, time) VALUES (?, ?)",
            (business, time)
        )
        await db.commit()
