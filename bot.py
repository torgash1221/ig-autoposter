import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from db import init_db
from scheduler import start_scheduler, load_schedule

from handlers import upload_router, publish_router


async def main():
    bot = Bot(BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()

    # 🔌 handlers
    dp.include_router(upload_router)
    dp.include_router(publish_router)

    # 🗄 DB
    await init_db()

    # ⏰ Scheduler
    OWNER_CHAT_ID = 123456789  # ← ВСТАВЬ СВОЙ chat_id
    await load_schedule(bot, OWNER_CHAT_ID)
    start_scheduler()

    print("🤖 Бот запущен")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
