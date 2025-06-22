import os
import secrets
import sqlite3
from typing import List

import aiosqlite
import uvicorn
from asyncpg.exceptions import UniqueViolationError
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from passlib.context import CryptContext

from app.config import load_config
from app.models.models import User, UserInDB, Todo

# === CONFIG & INIT ===

config = load_config()
# app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
security = HTTPBasic()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DOCS_USER = os.getenv("DOCS_USER")
DOCS_PASSWORD = os.getenv("DOCS_PASSWORD")

from fastapi import FastAPI, Depends
from pydantic import BaseModel
from database import get_db_connection
from database_sqlite import get_sqlite_connection
import asyncpg

app = FastAPI()


class Item(BaseModel):
    name: str

@app.post("/items")
async def create_item(item: Item, db: asyncpg.Connection = Depends(get_db_connection)):
    await db.execute('''
        INSERT INTO items(name) VALUES($1)
    ''', item.name)
    return {"message": "Item added successfully!"}


# @app.post('/register')
# async def register_user(user: User, db: aiosqlite.Connection = Depends(get_sqlite_connection)): # заменить sqlite3 на aiosqlite для асинхронности
#     await db.execute("""
#         INSERT INTO users (username, password) VALUES($1, $2)
#     """, (user.username, user.password))
#     await db.commit()
#     return {"message": "User registered successfully"}

@app.post('/register')
async def register_user(user: User, db: asyncpg.Connection = Depends(get_db_connection)): # заменить sqlite3 на aiosqlite для асинхронности
    await db.execute("""
        INSERT INTO users (username, password) VALUES($1, $2)
    """, user.username, user.password)
    return {"message": "User registered successfully"}

@app.delete('/delete_user/{user_id}')
async def delete_user(user_id: int, db: asyncpg.Connection = Depends(get_db_connection)): # заменить sqlite3 на aiosqlite для асинхронности
    result = await db.execute("""
            DELETE FROM users WHERE id = $1
        """, user_id)

    if result == "DELETE 0":
        return JSONResponse(status_code=404, content={"message": "User not found"})

    return {"message": "User and his todos are successfully deleted!"}


VALID_TABLES = {"users", "ThingsToDo"}

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

@app.post('/create_note')
async def create_note(note: Todo, db: asyncpg.Connection = Depends(get_db_connection)):
    if not await check_by_id(note.user_id, 'users', db):
        return JSONResponse(status_code=404, content={"message": "User not found"})
    try:
        await db.execute("""
            INSERT INTO ThingsToDo(id, title, description, completed, user_id)
            VALUES($1, $2, $3, $4, $5)
        """, note.id, note.title, note.description, note.completed, note.user_id)
        return {"message": "Item added with custom ID", "id": note.id}

    except UniqueViolationError:
        row = await db.fetchrow("""
            INSERT INTO ThingsToDo(title, description, completed, user_id)
            VALUES($1, $2, $3, $4)
            RETURNING id
        """, note.title, note.description, note.completed, note.user_id)
        return {"message": "ID already taken, inserted with auto ID", "id": row["id"]}

@app.get('/get_note/{note_id}', response_model=Todo)
async def get_note(note_id: int, db: asyncpg.Connection = Depends(get_db_connection)):
    res = await db.fetchrow("""
        SELECT * FROM ThingsToDo
        WHERE id = $1
    """, note_id)
    if res:
        return Todo(**dict(res))
    return JSONResponse(status_code=404, content={"message": "Item not found"})


@app.delete('/delete_note/{note_id}')
async def delete_note(note_id: int, db: asyncpg.Connection = Depends(get_db_connection)):
    result = await db.execute("""
        DELETE FROM ThingsToDo WHERE id = $1
    """, note_id)

    if result == "DELETE 0":
        return JSONResponse(status_code=404, content={"message": "Item not found"})

    return {"message": "Item successfully deleted!"}


@app.put('/update_note/{note_id}')
async def update_note(note_id: int, note: Todo, db: asyncpg.Connection = Depends(get_db_connection)):
    if not await check_by_id(note.user_id, 'users', db):
        return JSONResponse(status_code=404, content={"message": "User not found"})

    result = await db.execute("""
        UPDATE ThingsToDo
        SET title = $1, description = $2, completed=$3, user_id=$5
        WHERE id = $4
    """, note.title, note.description, note.completed, note_id, note.user_id)
    if result == 'UPDATE 1':
        return JSONResponse(status_code=200, content={"message": "Item successfully updated!"})
    return JSONResponse(status_code=404, content={"message": "Item not found."})


# === RUN ===

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
