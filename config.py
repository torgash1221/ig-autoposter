import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_CHAT_ID = int(os.getenv("OWNER_CHAT_ID", "0"))

TIMEZONE = "Europe/Kyiv"

BUSINESSES = {
    "ustritso": "🦪 УстриЦО",
    "mythai": "🍣 My Thai"
}
