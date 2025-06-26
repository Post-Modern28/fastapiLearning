import calendar
import logging
import os
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import asyncpg
import uvicorn
from asyncpg import UniqueViolationError

from app.security.security import verify_password, create_jwt_token, get_current_user
from exception_handlers import *
from exceptions import *
from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic
from fastapi_babel import Babel, BabelConfigs, BabelMiddleware, _

from security.security import get_password_hash, pwd_context
from helpers.db_helpers import get_table_columns, check_by_id
from app.config import load_config
from app.database.database import get_db_connection
from app.models.models import ItemsResponse, Todo, TodoReturn, User, UserInfo, UserRegistration, UserLogin

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
# import enable_translation

# === CONFIG & INIT ===

config = load_config()
security = HTTPBasic()


DOCS_USER = os.getenv("DOCS_USER")
DOCS_PASSWORD = os.getenv("DOCS_PASSWORD")


# Настроим базовый логгер
logging.basicConfig(level=logging.INFO)

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
# app.add_exception_handler(CustomException, custom_exception_handler)
# app.add_exception_handler(Exception, global_exception_handler)





# ===ROUTES===


# Пример использования перевода в эндпоинте
@app.get("/")
async def root():
    # Функция _() автоматически заменит "Hello World" на перевод
    return {"message": _("Hello World")}


@app.get("/sum/")
def calculate_sum(a: int, b: int):
    return {"result": a + b}

@app.get(
    "/items/{item_id}/",
    response_model=ItemsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Items by ID.",
    description="The endpoint returns item_id by ID. If the item_id is 42, an exception with the status code 404 is returned.",
    responses={
        status.HTTP_200_OK: {"model": ItemsResponse},
        status.HTTP_404_NOT_FOUND: {
            "model": CustomExceptionModel
        },  # вот тут применяем схемы ошибок пидантика
    },
)
async def read_item(item_id: int):
    if item_id == 42:
        raise CustomException(
            detail="Item not found",
            status_code=404,
            message="You're trying to get an item that doesn't exist. Try entering a different item_id.",
        )
    return ItemsResponse(item_id=item_id)



@app.post("/register", response_model=UserInfo, status_code=201)
@limiter.limit("5/minute")
async def register_user(
    request: Request,
    user: UserRegistration, db: asyncpg.Connection = Depends(get_db_connection)
):
    try:
        user_id = await db.fetchval("""
            INSERT INTO users (username, hashed_password)
            VALUES ($1, $2)
            RETURNING id
        """, user.username, get_password_hash(user.password))
    except UniqueViolationError:
        raise HTTPException(status_code=409, detail="User already exists.")
    print(user_id)

    await db.execute("""
        INSERT INTO user_info (user_id, full_name, email)
        VALUES ($1, $2, $3)
    """, user_id, user.full_name, user.email)

    return UserInfo(
        user_id=user_id,
        username=user.username,
        full_name=user.full_name,
        email=user.email
    )



@app.post("/log_in")
@limiter.limit("5/minute")
async def log_in(
    request: Request,
    user: UserLogin, db: asyncpg.Connection = Depends(get_db_connection)
):
    try:
        real_pass = await db.fetchval("""
        SELECT hashed_password 
        FROM users
        WHERE username = $1
        """, user.username)
        if not real_pass:
            raise HTTPException(status_code=401, detail="User not found")
    except:
        raise HTTPException(status_code=500, detail="Server Error")

    if not verify_password(user.password, real_pass):
        raise HTTPException(status_code=401, detail="Incorrect password")
    token = create_jwt_token({"sub": user.username})
    response = JSONResponse(
        content={"access_token": token, "token_type": "bearer",
                 "message": f"Welcome, {user.username}"},
    )
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response

@app.post("/get_user/{user_id}")
async def get_user(
    request: Request,
    user_id: int, db: asyncpg.Connection = Depends(get_db_connection)
):
    res = await db.fetchrow(
        """
        SELECT *, username 
        FROM user_info
        JOIN users ON users.id = user_info.user_id
        WHERE user_id = $1
    """,
        user_id
    )
    print(res)
    if not res:
        return JSONResponse(status_code=404, content={"message": "User not found"})
    return UserInfo(**dict(res))

@app.get("/protected")
async def protected(
    request: Request,
    username: str = Depends(get_current_user)
):
    return {"message": f"Hello, {username}"}

@app.post("/get_users")
async def get_users(
    db: asyncpg.Connection = Depends(get_db_connection)
):
    res = await db.fetch(
    """
        SELECT * 
        FROM user_info 
    """
    )
    if not res:
        return JSONResponse(status_code=404, content={"message": "Users not found"})
    return [UserInfo(**dict(usr)) for usr in res]


@app.delete("/delete_user/{user_id}")
async def delete_user(
    user_id: int, db: asyncpg.Connection = Depends(get_db_connection)
):
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
