from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from content_picker import pick_content
from db import DB_NAME
import aiosqlite

scheduler = AsyncIOScheduler()

async def send_story(bot, chat_id, business):
    content_id = await pick_content(business)
    if not content_id:
        await bot.send_message(chat_id, f"❌ Нет контента для {business}")
        return

    async with aiosqlite.connect(DB_NAME) as db:
        row = await db.execute_fetchone(
            "SELECT file_id FROM content WHERE id=?",
            (content_id,)
        )

        await db.execute(
            "UPDATE content SET used_count = used_count + 1, last_used=? WHERE id=?",
            (datetime.utcnow().isoformat(), content_id)
        )
        await db.commit()

    await bot.send_photo(
        chat_id,
        row[0],
        caption=f"📢 Пора публиковать сторис ({business})",
        reply_markup={
            "inline_keyboard": [
                [{"text": "📲 Опубликовать", "url": "https://www.instagram.com"}],
                [{"text": "🔁 Заменить", "callback_data": f"replace:{business}"}]
            ]
        }
    )
