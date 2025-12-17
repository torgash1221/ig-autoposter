from aiogram import Router, F
from aiogram.types import Message
import aiosqlite

from db import DB_NAME
from config import BUSINESSES
from handlers.state import user_business_state

router = Router()


@router.message(F.photo)
async def upload_photo(message: Message):
    user_id = message.from_user.id

    business = user_business_state.get(user_id)
    if not business:
        await message.answer("❗ Сначала выбери бизнес (/schedule_...)")
        return

    file_id = message.photo[-1].file_id

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO content (business, file_id) VALUES (?, ?)",
            (business, file_id)
        )
        await db.commit()

    await message.answer(
        f"✅ Контент сохранён для {BUSINESSES[business]}"
    )
