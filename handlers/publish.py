from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto
import aiosqlite
from datetime import datetime

from db import DB_NAME
from content_picker import pick_content
from config import BUSINESSES
from handlers.keyboards import publish_keyboard  # если вынес клавиатуру

router = Router()


# 🔁 ЗАМЕНИТЬ КОНТЕНТ
@router.callback_query(F.data.startswith("replace:"))
async def replace_content(callback: CallbackQuery):
    business = callback.data.split(":")[1]

    content_id = await pick_content(business)
    if not content_id:
        await callback.answer("❌ Нет другого контента", show_alert=True)
        return

    async with aiosqlite.connect(DB_NAME) as db:
        row = await db.execute_fetchone(
            "SELECT id, file_id FROM content WHERE id=?",
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

    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=row[1],
            caption=(
                f"📢 Пора публиковать сторис\n"
                f"Бизнес: {BUSINESSES[business]}"
            )
        ),
        reply_markup=publish_keyboard(business, content_id)
    )

    await callback.answer("🔁 Контент заменён")


# 🗑 УДАЛИТЬ КОНТЕНТ
@router.callback_query(F.data.startswith("delete:"))
async def delete_content(callback: CallbackQuery):
    content_id = int(callback.data.split(":")[1])

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "DELETE FROM content WHERE id=?",
            (content_id,)
        )
        await db.commit()

    await callback.message.edit_caption("🗑 Контент удалён")
    await callback.answer("Удалено")


# ✅ ОТМЕТИТЬ КАК ВЫЛОЖЕНО
@router.callback_query(F.data.startswith("published:"))
async def mark_published(callback: CallbackQuery):
    business = callback.data.split(":")[1]

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT INTO publish_log (business, time)
            VALUES (?, ?)
            """,
            (business, datetime.utcnow().isoformat())
        )
        await db.commit()

    await callback.message.edit_caption(
        callback.message.caption + "\n\n✅ Сторис выложена"
    )

    await callback.answer("✅ Зафиксировано")
