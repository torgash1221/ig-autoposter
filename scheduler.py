from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import aiosqlite

from db import DB_NAME, get_schedule, mark_used
from content_picker import pick_content
from config import BUSINESSES

scheduler = AsyncIOScheduler()


async def send_story(bot, chat_id: int, business: str):
    """
    Выбирает контент и отправляет сторис в Telegram
    """
    content_id = await pick_content(business)
    if not content_id:
        await bot.send_message(
            chat_id,
            f"❌ Нет контента для {BUSINESSES.get(business, business)}"
        )
        return

    async with aiosqlite.connect(DB_NAME) as db:
        row = await db.execute_fetchone(
            "SELECT file_id FROM content WHERE id=?",
            (content_id,)
        )

    if not row:
        await bot.send_message(chat_id, "❌ Контент не найден в БД")
        return

    file_id = row[0]

    await mark_used(content_id)

    await bot.send_photo(
        chat_id,
        file_id,
        caption=(
            f"📢 Пора публиковать сторис\n"
            f"Бизнес: {BUSINESSES.get(business, business)}\n"
            f"⏰ {datetime.now().strftime('%H:%M')}"
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
                    },
                    {
                        "text": "✅ Выложено",
                        "callback_data": f"published:{business}:{content_id}"
                    }
                ]
            ]
        }
    )


def add_job(bot, chat_id: int, business: str, time_str: str):
    """
    Добавляет cron-задачу
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


async def load_schedule(bot, chat_id: int):
    """
    Загружает расписание из БД и регистрирует задачи
    """
    rows = await get_schedule()

    for business, time_str in rows:
        add_job(bot, chat_id, business, time_str)


def start_scheduler():
    if not scheduler.running:
        scheduler.start()
