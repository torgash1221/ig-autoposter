import logging
import re
from handlers.state import user_business_state

from aiogram import Router, F
from aiogram.types import Message

from db import add_schedule
from scheduler import add_job
from config import BUSINESSES, OWNER_CHAT_ID

log = logging.getLogger(__name__)

router = Router()

TIME_PATTERN = re.compile(r"^\d{2}:\d{2}$")

# временное состояние: user_id → business
schedule_state = {}


@router.message(F.text == "/schedule")
async def schedule_start(message: Message):
    if message.from_user.id != OWNER_CHAT_ID:
        return

    log.info("SCHEDULE MENU")

    text = "📅 Выбери бизнес:\n"
    for key in BUSINESSES:
        text += f"/schedule_{key}\n"

    await message.answer(text)


@router.message(F.text.startswith("/schedule_"))
async def schedule_business(message: Message):
    if message.from_user.id != OWNER_CHAT_ID:
        return

    business = message.text.replace("/schedule_", "")
    log.info(f"SCHEDULE START for {business}")

    if business not in BUSINESSES:
        await message.answer("❌ Неизвестный бизнес")
        return

    schedule_state[message.from_user.id] = business
    user_business_state[message.from_user.id] = business  # 🔥 ВАЖНО

    await message.answer(
        f"⏰ Введи время для {BUSINESSES[business]} в формате HH:MM\n\n"
        f"Пример: 18:00"
    )


@router.message(F.text.regexp(r"^\d{2}:\d{2}$"))
async def schedule_time(message: Message):
    user_id = message.from_user.id
    log.info(f"TIME INPUT: {message.text} from {user_id}")

    if user_id not in schedule_state:
        log.warning(f"NO STATE for user {user_id}")
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

    log.info(f"SCHEDULE SAVED: {business} at {time_str}")

    await message.answer(
        f"✅ Расписание сохранено\n\n"
        f"{BUSINESSES[business]}\n"
        f"⏰ Время: {time_str}\n"
        f"📅 Каждый день"
    )

