import random
from datetime import datetime
import aiosqlite
from db import DB_NAME

async def pick_content(business):
    async with aiosqlite.connect(DB_NAME) as db:
        rows = await db.execute_fetchall(
            "SELECT id, priority, used_count FROM content WHERE business=?",
            (business,)
        )

    if not rows:
        return None

    weighted = []
    for cid, priority, used in rows:
        weight = priority * (1 / (1 + used))
        weighted.append((cid, weight))

    ids, weights = zip(*weighted)
    return random.choices(ids, weights=weights, k=1)[0]
