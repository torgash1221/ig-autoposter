import aiosqlite
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from zoneinfo import ZoneInfo

from db import DB_NAME
from content_picker import pick_content
from config import TIMEZONE, BUSINESSES
from handlers.keyboards import publish_keyboard

scheduler = AsyncIOScheduler(timezone=ZoneInfo(TIMEZONE))


async def send_story(bot, chat_id, business):
    content_id = await pick_content(business)
    if not content_id:
        await bot.send_message(chat_id, f"❌ Нет контента для {BUSINESSES[business]}")
        return

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id, file_id FROM content WHERE id=?",
            (content_id,)
        )
        row = await cursor.fetchone()


        await db.execute(
            """
            UPDATE content
            SET used_count = used_count + 1,
                last_used = ?
            WHERE id = ?
            """,
            (datetime.utcnow().isoformat(), content_id)
        )
        await db.commit()

    await bot.send_photo(
        chat_id=chat_id,
        photo=row[1],
        caption=(
            f"📢 Пора публиковать сторис\n"
            f"Бизнес: {BUSINESSES[business]}"
        ),
        reply_markup=publish_keyboard(business, content_id)
    )


def add_job(bot, chat_id, business, time_str):
    hour, minute = map(int, time_str.split(":"))

    scheduler.add_job(
        send_story,
        "cron",
        hour=hour,
        minute=minute,
        args=[bot, chat_id, business],
        id=f"{business}_{hour}_{minute}",
        replace_existing=True
    )


async def load_schedule(bot, chat_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT business, time FROM schedule"
        )
        rows = await cursor.fetchall()

    for business, time_str in rows:
        add_job(bot, chat_id, business, time_str)


def start_scheduler():
    if not scheduler.running:
        scheduler.start()
