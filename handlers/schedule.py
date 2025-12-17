from aiogram import Router, F
from aiogram.types import Message
import re

from db import add_schedule
from scheduler import add_job
from config import BUSINESSES, OWNER_CHAT_ID

router = Router()

TIME_PATTERN = re.compile(r"^\d{2}:\d{2}$")

# ✅ временное состояние: user_id → business
schedule_state = {}


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

    # ✅ сохраняем бизнес во временный state
    schedule_state[message.from_user.id] = business

    await message.answer(
        f"⏰ Введи время для {BUSINESSES[business]} в формате HH:MM\n\n"
        f"Пример: 18:00"
    )


@router.message()
async def schedule_time(message: Message):
    user_id = message.from_user.id

    # ✅ если пользователь не в режиме ввода времени — выходим
    if user_id not in schedule_state:
        return

    time_str = message.text.strip()

    if not TIME_PATTERN.match(time_str):
        await message.answer("❌ Неверный формат. Пример: 18:00")
        return

    business = schedule_state.pop(user_id)

    # 💾 сохраняем в БД
    await add_schedule(business, time_str)

    # ⏰ добавляем задачу сразу
    add_job(
        bot=message.bot,
        chat_id=OWNER_CHAT_ID,
        business=business,
        time_str=time_str
    )

    # ✅ ВОТ ТО САМОЕ ПОДТВЕРЖДЕНИЕ
    await message.answer(
        f"✅ Расписание сохранено\n\n"
        f"{BUSINESSES[business]}\n"
        f"⏰ Время: {time_str}\n"
        f"📅 Каждый день"
    )
