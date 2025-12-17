from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto
import aiosqlite

from db import DB_NAME
from config import BUSINESSES

router = Router()


@router.callback_query(F.data == "gallery")
async def open_gallery(callback: CallbackQuery):
    from handlers.keyboards import gallery_keyboard
    await callback.message.answer(
        "📂 Выбери бизнес",
        reply_markup=gallery_keyboard()
    )


@router.callback_query(F.data.startswith("gallery:"))
async def show_gallery(callback: CallbackQuery):
    business = callback.data.split(":")[1]

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT file_id FROM content
            WHERE business=?
            ORDER BY id DESC
            LIMIT 10
            """,
            (business,)
        )
        rows = await cursor.fetchall()

    if not rows:
        await callback.answer("❌ Контента нет", show_alert=True)
        return

    media = [
        InputMediaPhoto(media=row[0])
        for row in rows
    ]

    await callback.message.answer_media_group(media)
