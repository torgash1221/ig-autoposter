print("🔥🔥🔥 UPLOAD.PY LOADED 🔥🔥🔥")
from aiogram import Router, F
from aiogram.types import Message
import aiosqlite

from db import DB_NAME
from config import BUSINESSES
from handlers.state import user_business_state

router = Router()


def parse_tags(text: str) -> str:
    if not text:
        return ""
    text = text.replace("#", "")
    tags = [t.strip().lower() for t in text.split(",") if t.strip()]
    return ",".join(tags)


# ===== ВЫБОР БИЗНЕСА =====

@router.message(F.text.startswith("/upload_mythai"))
async def upload_mythai(message: Message):
    user_business_state[message.from_user.id] = "mythai"
    await message.answer("📤 Загружай контент для 🍣 My Thai")


@router.message(F.text.startswith("/upload_ustritso"))
async def upload_ustritso(message: Message):
    user_business_state[message.from_user.id] = "ustritso"
    await message.answer("📤 Загружай контент для 🦪 УстриЦО")


# ===== ЗАГРУЗКА ФОТО =====

@router.message(F.photo)
async def upload_photo(message: Message):
    user_id = message.from_user.id
    business = user_business_state.get(user_id)

    if not business:
        await message.answer(
            "❗ Сначала выбери бизнес:\n"
            "/upload_mythai\n"
            "/upload_ustritso"
        )
        return

    file_id = message.photo[-1].file_id
    tags = parse_tags(message.caption or "")

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT INTO content (business, file_id, tags)
            VALUES (?, ?, ?)
            """,
            (business, file_id, tags)
        )
        await db.commit()

    await message.answer(
        f"✅ Контент сохранён для {BUSINESSES[business]}\n"
        f"🏷 Теги: {tags or 'без тегов'}"
    )
