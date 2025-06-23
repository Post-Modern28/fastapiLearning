# import sqlite3
# заменить sqlite3 на aiosqlite для асинхронности
import aiosqlite

DB_NAME = "database.sqlite"


async def get_sqlite_connection():
    async with aiosqlite.connect(DB_NAME) as conn:
        conn.row_factory = aiosqlite.Row
        yield conn
