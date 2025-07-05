import asyncpg
from fastapi.exceptions import HTTPException

from app.core.config import load_config

config = load_config()
DATABASE_URL = config.db.database_url

VALID_TABLES = {"users", "ThingsToDo", "user_info", "user_roles"}


async def get_db_connection():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        await conn.close()




