import os
import secrets
import sqlite3
from typing import List

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from passlib.context import CryptContext

from app.config import load_config
from app.models.models import User, UserInDB

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
def register_user(user: User, db: sqlite3.Connection = Depends(get_sqlite_connection)): # заменить sqlite3 на aiosqlite для асинхронности
    db.execute("""
        INSERT INTO users (username, password) VALUES($1, $2)
    """, (user.username, user.password))
    db.commit()
    return {"message": "User registered successfully"}


# === RUN ===

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
