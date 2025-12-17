
from aiogram import Router, F
from aiogram.types import Message
import re

from db import add_schedule
from scheduler import add_job
from config import BUSINESSES, OWNER_CHAT_ID
logging.getLogger("aiogram").setLevel(logging.DEBUG)

router = Router()

TIME_PATTERN = re.compile(r"^\d{2}:\d{2}$")

# временное состояние: user_id → business
schedule_state = {}


@router.message(F.text == "/schedule")
async def schedule_start(message: Message):
    if message.from_user.id != OWNER_CHAT_ID:
        return

    text = "📅 Выбери бизнес:\n"
    for key in BUSINESSES:
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

    schedule_state[message.from_user.id] = business

    await message.answer(
        f"⏰ Введи время для {BUSINESSES[business]} в формате HH:MM\n\n"
        f"Пример: 18:00"
    )


@router.message(F.text.regexp(r"^\d{2}:\d{2}$"))
async def schedule_time(message: Message):
    user_id = message.from_user.id

    if user_id not in schedule_state:
        return

    time_str = message.text.strip()
    business = schedule_state.pop(user_id)

    await add_schedule(business, time_str)

    add_job(
        bot=message.bot,
        chat_id=OWNER_CHAT_ID,
        business=business,
        time_str=time_str
    )

    await message.answer(
        f"✅ Расписание сохранено\n\n"
        f"{BUSINESSES[business]}\n"
        f"⏰ Время: {time_str}\n"
        f"📅 Каждый день"
    )
