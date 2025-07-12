import calendar
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status, Form
from fastapi.responses import JSONResponse, RedirectResponse

from app.api.schemas.models import RoleEnum, Todo, TodoReturn, UserRole
from app.common.templates import templates
from app.database.database import get_db_connection
from app.database.repositories.note_repository import NoteRepository
from app.database.repositories.user_repository import UserRepository
from app.helpers.db_helpers import check_by_id, get_table_columns
from app.security.rbac import OwnershipChecker, PermissionChecker
from app.security.security import get_current_user_with_roles

todo_router = APIRouter(prefix="/notes", tags=["Notes"])

@todo_router.get("/create_note", status_code=status.HTTP_201_CREATED)
@PermissionChecker([RoleEnum.ADMIN, RoleEnum.USER])
async def create_note(
    request: Request,
    current_user: UserRole = Depends(get_current_user_with_roles),
    db: asyncpg.Connection = Depends(get_db_connection),
):
    repo = NoteRepository(db)
    return templates.TemplateResponse(
        "NewNote.html",
        {
            "request": request,
            "user": current_user,
        },
    )



@todo_router.post("/create_note", status_code=status.HTTP_201_CREATED)
@PermissionChecker([RoleEnum.ADMIN, RoleEnum.USER])
async def create_note(
    title: str = Form(...),
    description: str = Form(...),
    current_user: UserRole = Depends(get_current_user_with_roles),
    db: asyncpg.Connection = Depends(get_db_connection),
):
    repo = NoteRepository(db)
    row = await repo.create_note(title, description, current_user.user_id)
    return RedirectResponse("/notes/my_notes", status_code=status.HTTP_302_FOUND)


@todo_router.get("/my_notes", status_code=status.HTTP_200_OK)
@PermissionChecker([RoleEnum.ADMIN, RoleEnum.USER])
async def get_user_notes(
    request: Request,
    current_user: UserRole = Depends(get_current_user_with_roles),
    db: asyncpg.Connection = Depends(get_db_connection),
):
    user_repo = UserRepository(db)
    user_info = await user_repo.get_user_full_info(current_user.user_id)
    repo = NoteRepository(db)
    rows = await repo.get_user_notes(current_user.user_id)
    return templates.TemplateResponse(
        "MyNotes.html",
        {
            "request": request,
            "user": current_user,
            "user_profile": user_info,
            "todos": rows,
        },
    )


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
    repo = NoteRepository(db)
    column = sort_by.lstrip("-")
    order = "DESC" if sort_by.startswith("-") else "ASC"

    allowed = await get_table_columns("thingstodo", db)
    if column not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid sort field"
        )

    params = [limit, offset]
    clauses = ["TRUE"]

    if completed is not None:
        clauses.append(f"completed = ${len(params) + 1}")
        params.append(completed)
    if user_id is not None:
        if not await check_by_id(user_id, "users", db):
            raise HTTPException(status_code=400, detail="User not found")
        clauses.append(f"user_id = ${len(params) + 1}")
        params.append(user_id)
    if created_before:
        clauses.append(f"created_at <= ${len(params) + 1}")
        params.append(created_before)
    if created_after:
        clauses.append(f"created_at >= ${len(params) + 1}")
        params.append(created_after)
    if title_contains:
        clauses.append(f"title ILIKE ${len(params) + 1}")
        params.append(f"%{title_contains}%")

    query = f"""
        SELECT * FROM ThingsToDo
        WHERE {' AND '.join(clauses)}
        ORDER BY {column} {order}
        LIMIT $1
        OFFSET $2
    """

    res = await repo.get_filtered_notes(query, params)
    if not res:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Items not found"},
        )
    return [TodoReturn(**row) for row in res]


@todo_router.get("/get_note/{note_id}", response_model=TodoReturn)
@OwnershipChecker()
async def get_note_by_id(
    note_id: int,
    current_user: UserRole = Depends(get_current_user_with_roles),
    db: asyncpg.Connection = Depends(get_db_connection),
):
    repo = NoteRepository(db)
    row = await repo.get_note_by_id(note_id)
    if not row:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, content={"message": "Item not found"}
        )
    return TodoReturn(**dict(row))


@todo_router.post("/delete/{note_id}")
@todo_router.delete("/delete/{note_id}")
@PermissionChecker([RoleEnum.ADMIN, RoleEnum.USER])
@OwnershipChecker()
async def delete_note(
    note_id: int,
    current_user: UserRole = Depends(get_current_user_with_roles),
    db: asyncpg.Connection = Depends(get_db_connection),
):
    repo = NoteRepository(db)
    result = await repo.delete_note(note_id)
    if result == "DELETE 0":
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, content={"message": "Item not found"}
        )
    return RedirectResponse("/notes/my_notes", status_code=status.HTTP_302_FOUND)


@todo_router.put("/update_note/{note_id}")
@OwnershipChecker()
async def update_note(
    note_id: int,
    note: Todo,
    current_user: UserRole = Depends(get_current_user_with_roles),
    db: asyncpg.Connection = Depends(get_db_connection),
):
    repo = NoteRepository(db)
    result = await repo.update_note(
        note_id, note.title, note.description, note.completed
    )
    if result == "UPDATE 1":
        return {"message": "Item successfully updated!"}
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND, content={"message": "Item not found."}
    )

@todo_router.post("/complete/{note_id}")
@OwnershipChecker()
async def complete_note(
    note_id: int,
    current_user: UserRole = Depends(get_current_user_with_roles),
    db: asyncpg.Connection = Depends(get_db_connection),
):
    repo = NoteRepository(db)
    result = await repo.complete_note(note_id)

    return RedirectResponse("/notes/my_notes", status_code=status.HTTP_302_FOUND)



@todo_router.patch("/complete_notes")
async def complete_notes(
    note_id: list[int] = Query(...),
    completed: bool = True,
    db: asyncpg.Connection = Depends(get_db_connection),
):
    repo = NoteRepository(db)
    result = await repo.bulk_complete(note_id, completed)
    num = result.split()[1]
    return {"updated_count": int(num)}


@todo_router.get("/analytics")
async def get_todos_analytics(
    timezone: str = Query("Europe/Moscow"),
    db: asyncpg.Connection = Depends(get_db_connection),
):
    try:
        ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid timezone")

    repo = NoteRepository(db)
    total, status_counts, avg_time, weekday_raw = await repo.get_analytics(timezone)

    completed_stats = {
        str(row["completed"]).lower(): row["count"] for row in status_counts
    }
    weekday_distribution = {row["weekday"].strip(): row["count"] for row in weekday_raw}
    full_weekday_distribution = {
        day: weekday_distribution.get(day, 0) for day in calendar.day_name
    }

    return {
        "total": total,
        "completed_stats": completed_stats,
        "avg_completion_time_hours": round(avg_time, 2) if avg_time else 0.0,
        "weekday_distribution": full_weekday_distribution,
    }
