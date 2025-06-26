import asyncpg
from fastapi import HTTPException

from app.database.database import VALID_TABLES


async def get_table_columns(table_name: str, db: asyncpg.Connection) -> list[str]:
    rows = await db.fetch(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = $1
    """,
        table_name,
    )
    return [row["column_name"] for row in rows]


async def check_by_id(item_id: int, table_name: str, db: asyncpg.Connection):
    """
    Checks whether item with such ID exists in a table
    :return: True if item exists in table, False otherwise
    """
    if table_name not in VALID_TABLES:
        raise HTTPException(status_code=400, detail="Invalid table name")

    query = f"SELECT * FROM {table_name} WHERE id = $1"
    item_exists = await db.fetchrow(query, item_id)
    return bool(item_exists)
