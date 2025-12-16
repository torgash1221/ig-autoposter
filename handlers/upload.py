from aiogram import Router, F
from aiogram.types import Message
import aiosqlite
from db import DB_NAME

router = Router()

@router.message(F.photo)
async def upload_photo(message: Message):
    file_id = message.photo[-1].file_id
    text = message.caption or ""

    business = "ustritso" if "устри" in text.lower() else "mythai"

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO content (business, file_id) VALUES (?, ?)",
            (business, file_id)
        )
        await db.commit()

    await message.answer(f"✅ Контент сохранён для {business}")
