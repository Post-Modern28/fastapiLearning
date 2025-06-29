from fastapi.exceptions import HTTPException

import asyncpg

from app.config import load_config

config = load_config()
DATABASE_URL = config.db.database_url

VALID_TABLES = {"users", "ThingsToDo"}


async def get_db_connection():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        await conn.close()

async def get_note_owner(note_id: int, db: asyncpg.Connection) -> int:
    row = await db.fetchrow(
        "SELECT user_id FROM ThingsToDo WHERE id = $1",
        note_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return row["user_id"]


# async def get_note_owners(note_id: list[int], db: asyncpg.Connection) -> int:
#     rows = await db.fetch(
#         "SELECT user_id FROM ThingsToDo WHERE id = ANY($1::int[])",
#         note_id,
#     )
#     if rows is None:
#         raise HTTPException(status_code=404, detail="Notes not found")
#     return rows["user_id"]