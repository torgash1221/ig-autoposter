import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logging.getLogger("aiogram").setLevel(logging.DEBUG)


from config import BOT_TOKEN, OWNER_CHAT_ID
from db import init_db
from scheduler import start_scheduler, load_schedule
from handlers import upload_router, publish_router, schedule_router


async def main():
    bot = Bot(
        BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        )
    )

    dp = Dispatcher()

    # handlers

    dp.include_router(schedule_router)   # 🔥 ПЕРВЫМ
    dp.include_router(upload_router)
    dp.include_router(publish_router)


    # DB
    await init_db()

    # Scheduler
    await load_schedule(bot, OWNER_CHAT_ID)
    start_scheduler()

    print("🤖 Бот запущен и scheduler активен")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
