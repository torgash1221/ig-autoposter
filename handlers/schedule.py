from aiogram import Router, F
from aiogram.types import Message
import re

from db import add_schedule
from scheduler import add_job
from config import BUSINESSES, OWNER_CHAT_ID

router = Router()

TIME_PATTERN = re.compile(r"^\d{2}:\d{2}$")


@router.message(F.text == "/schedule")
async def schedule_start(message: Message):
    if message.from_user.id != OWNER_CHAT_ID:
        return

    text = "📅 Выбери бизнес:\n"
    for key, name in BUSINESSES.items():
        text += f"/schedule_{key}\n"

    await message.answer(text)


@router.message(F.text.startswith("/schedule_"))
async def schedule_business(message: Message):
    if message.from_user.id != OWNER_CHAT_ID:
        return

    business = message.text.replace("/schedule_", "")
    if business not in BUSINESSES:
        await message.answer("❌ Неизвестный бизнес")
        return

    await message.answer(
        f"⏰ Введи время для {BUSINESSES[business]} в формате HH:MM\n\n"
        f"Пример: 18:00"
    )

    # сохраняем выбранный бизнес во временный state
    message.bot_data[message.from_user.id] = business


@router.message()
async def schedule_time(message: Message):
    user_id = message.from_user.id

    if user_id not in message.bot_data:
        return

    time_str = message.text.strip()

    if not TIME_PATTERN.match(time_str):
        await message.answer("❌ Неверный формат. Пример: 18:00")
        return

    business = message.bot_data.pop(user_id)

    # сохраняем в БД
    await add_schedule(business, time_str)

    # добавляем задачу сразу
    add_job(
        bot=message.bot,
        chat_id=OWNER_CHAT_ID,
        business=business,
        time_str=time_str
    )

    await message.answer(
        f"✅ Расписание добавлено:\n"
        f"{BUSINESSES[business]} — {time_str}"
    )
