import os
import secrets
import sqlite3
from typing import List

import aiosqlite
import uvicorn
from asyncpg import UniqueViolationError
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


@app.post('/register')
async def register_user(user: User, db: aiosqlite.Connection = Depends(get_sqlite_connection)): # заменить sqlite3 на aiosqlite для асинхронности
    await db.execute("""
        INSERT INTO users (username, password) VALUES($1, $2)
    """, (user.username, user.password))
    await db.commit()
    return {"message": "User registered successfully"}


@app.post('/create_note')
async def create_note(note: Todo, db: asyncpg.Connection = Depends(get_db_connection)):
    try:
        await db.execute("""
            INSERT INTO ThingsToDo(id, title, description, completed)
            VALUES($1, $2, $3, $4)
        """, note.id, note.title, note.description, note.completed)
        return {"message": "Item added with custom ID", "id": note.id}

    except UniqueViolationError:
        row = await db.fetchrow("""
            INSERT INTO ThingsToDo(title, description, completed)
            VALUES($1, $2, $3)
            RETURNING id
        """, note.title, note.description, note.completed)
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
    result = await db.execute("""
        UPDATE ThingsToDo
        SET title = $1, description = $2, completed=$3
        WHERE id = $4
    """, note.title, note.description, note.completed, note_id)
    if result == 'UPDATE 1':
        return JSONResponse(status_code=200, content={"message": "Item successfully updated!"})
    return JSONResponse(status_code=404, content={"message": "Item not found."})

# === RUN ===

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
