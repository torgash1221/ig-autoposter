from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import aiosqlite

from content_picker import pick_content
from db import DB_NAME
from config import BUSINESSES

scheduler = AsyncIOScheduler()


async def send_story(bot, chat_id: int, business: str):
    """
    Выбирает контент и отправляет его в Telegram
    """
    content_id = await pick_content(business)
    if not content_id:
        await bot.send_message(
            chat_id,
            f"❌ Нет контента для {BUSINESSES[business]}"
        )
        return

    async with aiosqlite.connect(DB_NAME) as db:
        row = await db.execute_fetchone(
            "SELECT file_id FROM content WHERE id=?",
            (content_id,)
        )

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
        chat_id,
        row[0],
        caption=(
            f"📢 Пора публиковать сторис\n"
            f"Бизнес: {BUSINESSES[business]}"
        ),
        reply_markup={
            "inline_keyboard": [
                [
                    {
                        "text": "📲 Опубликовать сторис",
                        "url": "https://www.instagram.com"
                    }
                ],
                [
                    {
                        "text": "🔁 Заменить",
                        "callback_data": f"replace:{business}"
                    }
                ]
            ]
        }
    )


def schedule_story(bot, chat_id: int, business: str, time_str: str):
    """
    Добавляет задачу в планировщик
    time_str = '18:00'
    """
    hour, minute = map(int, time_str.split(":"))

    scheduler.add_job(
        send_story,
        trigger="cron",
        hour=hour,
        minute=minute,
        args=[bot, chat_id, business],
        id=f"{business}_{time_str}",
        replace_existing=True
    )


def start_scheduler():
    if not scheduler.running:
        scheduler.start()
