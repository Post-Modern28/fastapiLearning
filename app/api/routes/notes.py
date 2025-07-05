import calendar
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.api.schemas.models import (
    RoleEnum,
    Todo,
    TodoReturn,
    UserRole,
)

# from fastapi_babel import Babel, BabelConfigs, BabelMiddleware, _
from app.database.database import get_db_connection
from app.helpers.db_helpers import check_by_id, get_table_columns
from app.security.rbac import OwnershipChecker, PermissionChecker
from app.security.security import (
    get_current_user_with_roles,
)

todo_router = APIRouter(prefix="/notes", tags=["Notes"])


@todo_router.post("/create_note", status_code=201)
@PermissionChecker([RoleEnum.ADMIN, RoleEnum.USER])
async def create_note(
    note: Todo,
    current_user: UserRole = Depends(get_current_user_with_roles),
    db: asyncpg.Connection = Depends(get_db_connection),
):

    row = await db.fetchrow(
        """
        INSERT INTO ThingsToDo(title, description, user_id)
        VALUES($1, $2, $3)
        RETURNING *
    """,
        note.title,
        note.description,
        current_user.user_id,
    )
    return {"message": "Note created", "item": TodoReturn(**row)}


@todo_router.get("/get_notes", response_model=list[TodoReturn])
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


@todo_router.get("/get_note/{note_id}", response_model=TodoReturn)
@OwnershipChecker()
async def get_note(
    note_id: int,
    current_user: UserRole = Depends(get_current_user_with_roles),
    db: asyncpg.Connection = Depends(get_db_connection),
):
    res = await db.fetchrow(
        """
        SELECT * FROM ThingsToDo
        WHERE id = $1
    """,
        note_id,
    )
    if res:
        print(res)
        return TodoReturn(**dict(res))
    return JSONResponse(status_code=404, content={"message": "Item not found"})


@todo_router.delete("/delete_note/{note_id}")
@PermissionChecker([RoleEnum.ADMIN, RoleEnum.USER])
@OwnershipChecker()
async def delete_note(
    note_id: int,
    current_user: UserRole = Depends(get_current_user_with_roles),
    db: asyncpg.Connection = Depends(get_db_connection),
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


@todo_router.put("/update_note/{note_id}")
@OwnershipChecker()
async def update_note(
    note_id: int,
    note: Todo,
    current_user: UserRole = Depends(get_current_user_with_roles),
    db: asyncpg.Connection = Depends(get_db_connection),
):

    result = await db.execute(
        """
        UPDATE ThingsToDo
        SET title = $1, description = $2, completed=$3
        WHERE id = $4
    """,
        note.title,
        note.description,
        note.completed,
        note_id,
    )
    if result == "UPDATE 1":
        return JSONResponse(
            status_code=200, content={"message": "Item successfully updated!"}
        )
    return JSONResponse(status_code=404, content={"message": "Item not found."})


@todo_router.patch("/complete_notes")
async def complete_notes(
    note_id: list[int] = Query(...),
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
        note_id,
    )
    num_updated = result.split()[1]
    return JSONResponse(content={"updated_count": int(num_updated)})


@todo_router.get("/notes/analytics")
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
