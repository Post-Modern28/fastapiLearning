import sqlite3 # заменить sqlite3 на aiosqlite для асинхронности

DB_NAME = "database.sqlite"


def get_sqlite_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Это позволяет получать данные в виде словаря
    return conn

