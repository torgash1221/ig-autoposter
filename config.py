import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

BUSINESSES = {
    "ustritso": "🦪 УстриЦО",
    "mythai": "🍣 My Thai"
}
