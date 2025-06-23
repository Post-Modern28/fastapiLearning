import calendar
import os
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import asyncpg
import uvicorn
from exception_handlers import *
from exceptions import *
from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic
from passlib.context import CryptContext

from app.config import load_config
from app.database.database import VALID_TABLES, get_db_connection
from app.models.models import Todo, TodoReturn, User, ItemsResponse

# ===HELPERS===


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


def parse_custom_datetime(value: Optional[str] = Query(None)) -> Optional[datetime]:
    print("Value is", value)
    if value is None:
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d.%m.%Y %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError("Неверный формат даты")


# === CONFIG & INIT ===

config = load_config()
security = HTTPBasic()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DOCS_USER = os.getenv("DOCS_USER")
DOCS_PASSWORD = os.getenv("DOCS_PASSWORD")

import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

# Настроим базовый логгер
logging.basicConfig(level=logging.INFO)

app = FastAPI()
app.add_exception_handler(CustomException, custom_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# @app.exception_handler(Exception)



@app.get(
    "/items/{item_id}/",
    response_model=ItemsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Items by ID.",
    description="The endpoint returns item_id by ID. If the item_id is 42, an exception with the status code 404 is returned.",
    responses={
        status.HTTP_200_OK: {'model': ItemsResponse},
        status.HTTP_404_NOT_FOUND: {'model': CustomExceptionModel},  # вот тут применяем схемы ошибок пидантика
    },
)
async def read_item(item_id: int):
    if item_id == 42:
        raise CustomException(detail="Item not found", status_code=404, message="You're trying to get an item that doesn't exist. Try entering a different item_id.")
    return ItemsResponse(item_id=item_id)


@app.post("/register")
async def register_user(
    user: User, db: asyncpg.Connection = Depends(get_db_connection)
):  # заменить sqlite3 на aiosqlite для асинхронности
    await db.execute(
        """
        INSERT INTO users (username, password) VALUES($1, $2)
    """,
        user.username,
        user.password,
    )
    return {"message": "User registered successfully"}


@app.delete("/delete_user/{user_id}")
async def delete_user(
    user_id: int, db: asyncpg.Connection = Depends(get_db_connection)
):  # заменить sqlite3 на aiosqlite для асинхронности
    result = await db.execute(
        """
            DELETE FROM users WHERE id = $1
        """,
        user_id,
    )

    if result == "DELETE 0":
        return JSONResponse(status_code=404, content={"message": "User not found"})

    return {"message": "User and his todos are successfully deleted!"}


@app.post("/create_note")
async def create_note(note: Todo, db: asyncpg.Connection = Depends(get_db_connection)):
    if not await check_by_id(note.user_id, "users", db):
        return JSONResponse(status_code=404, content={"message": "User not found"})

    row = await db.fetchrow(
        """
        INSERT INTO ThingsToDo(title, description, user_id)
        VALUES($1, $2, $3)
        RETURNING *
    """,
        note.title,
        note.description,
        note.user_id,
    )
    return {"message": "Item added with custom ID", "item": TodoReturn(**row)}


@app.get("/get_notes", response_model=list[TodoReturn])
async def get_note(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = "id",
    completed: Optional[bool] = Query(None),
    user_id: Optional[int] = Query(None),
    created_before: Optional[datetime] = Query(None),
    created_after: Optional[datetime] = Query(None),
    title_contains: Optional[str] = Query(None),
    db: asyncpg.Connection = Depends(get_db_connection),
):
    order = "DESC" if sort_by.startswith("-") else "ASC"
    column = sort_by.lstrip("-")
    allowed_sort_fields = await get_table_columns("thingstodo", db)
    if column not in allowed_sort_fields:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    params = [limit, offset]
    where_clauses = ["TRUE"]

    if completed is not None:
        where_clauses.append(f"completed = ${len(params) + 1}")
        params.append(completed)

    if user_id is not None:
        if not await check_by_id(user_id, "users", db):
            raise HTTPException(status_code=400, detail="User not found")
        where_clauses.append(f"user_id = ${len(params) + 1}")
        params.append(user_id)

    if created_before is not None:
        where_clauses.append(f"created_at <= ${len(params) + 1}")
        params.append(created_before)

    if created_after is not None:
        where_clauses.append(f"created_at >= ${len(params) + 1}")
        params.append(created_after)

    if title_contains:
        where_clauses.append(f"title ILIKE ${len(params) + 1}")
        params.append(f"%{title_contains}%")

    query = f"""
        SELECT * FROM ThingsToDo
        WHERE {' AND '.join(where_clauses)}
        ORDER BY {column} {order}
        LIMIT $1
        OFFSET $2
    """

    res = await db.fetch(query, *params)
    if not res:
        return JSONResponse(status_code=404, content={"message": "Items not found"})
    return [TodoReturn(**row) for row in res]


@app.get("/get_note/{note_id}", response_model=Todo)
async def get_note(note_id: int, db: asyncpg.Connection = Depends(get_db_connection)):
    res = await db.fetchrow(
        """
        SELECT * FROM ThingsToDo
        WHERE id = $1
    """,
        note_id,
    )
    if res:
        return Todo(**dict(res))
    return JSONResponse(status_code=404, content={"message": "Item not found"})


@app.delete("/delete_note/{note_id}")
async def delete_note(
    note_id: int, db: asyncpg.Connection = Depends(get_db_connection)
):
    result = await db.execute(
        """
        DELETE FROM ThingsToDo WHERE id = $1
    """,
        note_id,
    )

    if result == "DELETE 0":
        return JSONResponse(status_code=404, content={"message": "Item not found"})

    return {"message": "Item successfully deleted!"}


@app.put("/update_note/{note_id}")
async def update_note(
    note_id: int, note: Todo, db: asyncpg.Connection = Depends(get_db_connection)
):
    if not await check_by_id(note.user_id, "users", db):
        return JSONResponse(status_code=404, content={"message": "User not found"})

    result = await db.execute(
        """
        UPDATE ThingsToDo
        SET title = $1, description = $2, completed=$3, user_id=$5
        WHERE id = $4
    """,
        note.title,
        note.description,
        note.completed,
        note_id,
        note.user_id,
    )
    if result == "UPDATE 1":
        return JSONResponse(
            status_code=200, content={"message": "Item successfully updated!"}
        )
    return JSONResponse(status_code=404, content={"message": "Item not found."})


@app.patch("/complete_notes")
async def complete_notes(
    ids: list[int] = Query(...),
    completed: bool = True,
    db: asyncpg.Connection = Depends(get_db_connection),
):
    result = await db.execute(
        """
            UPDATE ThingsToDo
            SET completed = $1,
                completed_at = CASE WHEN $1 THEN CURRENT_TIMESTAMP ELSE NULL END
            WHERE id = ANY($2::int[])
        """,
        completed,
        ids,
    )
    num_updated = result.split()[1]
    return JSONResponse(content={"updated_count": int(num_updated)})


@app.get("/notes/analytics")
async def get_todos_analytics(
    timezone: str = Query("Europe/Moscow"),
    db: asyncpg.Connection = Depends(get_db_connection),
):
    try:
        ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        raise HTTPException(status_code=400, detail="Invalid timezone")

    total = await db.fetchval(
        """
        SELECT COUNT(*) 
        FROM ThingsToDo
        """
    )
    status_counts = await db.fetch(
        """
        SELECT completed, COUNT(*) as count 
        FROM ThingsToDo
        GROUP BY completed
    """
    )
    completed_stats = {
        str(row["completed"]).lower(): row["count"] for row in status_counts
    }
    avg_completion_time = await db.fetchval(
        """
        SELECT AVG(EXTRACT(EPOCH FROM (completed_at - created_at)) / 3600) 
        FROM ThingsToDo
        WHERE completed = true
    """
    )

    weekday_raw = await db.fetch(
        """
            SELECT
                to_char(created_at AT TIME ZONE $1, 'Day') as weekday,
                EXTRACT(DOW FROM created_at AT TIME ZONE $1) as dow,
                COUNT(*) as count
            FROM ThingsToDo
            GROUP BY weekday, dow
            ORDER BY dow
        """,
        timezone,
    )
    weekday_distribution = {}
    for row in weekday_raw:
        day_name = row["weekday"].strip()
        weekday_distribution[day_name] = row["count"]

    all_days = list(calendar.day_name)
    full_weekday_distribution = {
        day: weekday_distribution.get(day, 0) for day in all_days
    }

    return {
        "total": total,
        "completed_stats": completed_stats,
        "avg_completion_time_hours": (
            round(avg_completion_time, 2) if avg_completion_time else 0.0
        ),
        "weekday_distribution": full_weekday_distribution,
    }


# === RUN ===

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
