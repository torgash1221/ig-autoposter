async def pick_content(business, tag=None):
    async with aiosqlite.connect(DB_NAME) as db:
        if tag:
            cursor = await db.execute(
                """
                SELECT id FROM content
                WHERE business=? AND tags LIKE ?
                ORDER BY last_used ASC
                LIMIT 1
                """,
                (business, f"%{tag}%")
            )
        else:
            cursor = await db.execute(
                """
                SELECT id FROM content
                WHERE business=?
                ORDER BY last_used ASC
                LIMIT 1
                """,
                (business,)
            )

        row = await cursor.fetchone()
        return row[0] if row else None
