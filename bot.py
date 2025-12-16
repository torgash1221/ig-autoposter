import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from db import init_db
from handlers import upload, reports

async def main():
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(upload.router)
    dp.include_router(reports.router)

    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
