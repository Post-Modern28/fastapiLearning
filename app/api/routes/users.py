# app/api/routes/users.py

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
import asyncpg

from app.api.schemas.models import (
    RoleEnum,
    UserInfo,
    UserLogin,
    UserRegistration,
    UserRole,
)
from app.database.database import get_db_connection
from app.database.repositories.user_repository import UserRepository
from app.security.rbac import PermissionChecker, role_based_rate_limit
from app.security.security import (
    create_jwt_token,
    get_current_user_with_roles,
    get_password_hash,
    verify_password,
)

users_router = APIRouter(prefix="/users", tags=["Users"])


@users_router.post("/register", response_model=UserInfo, status_code=201)
async def register_user(
    request: Request,
    user: UserRegistration,
    db: asyncpg.Connection = Depends(get_db_connection),
):
    user_repo = UserRepository(db)
    user_id = await user_repo.create_user(user.username, get_password_hash(user.password))
    if user_id == -1:
        raise HTTPException(status_code=409, detail="User already exists.")

    await user_repo.create_user_info(user_id, user.full_name, user.email)
    await user_repo.assign_default_role(user_id)

    return UserInfo(
        user_id=user_id,
        username=user.username,
        full_name=user.full_name,
        email=user.email,
    )


@users_router.post("/log_in")
async def log_in(
    request: Request,
    user: UserLogin,
    db: asyncpg.Connection = Depends(get_db_connection),
):
    user_repo = UserRepository(db)

    try:
        row = await user_repo.get_user_by_username(user.username)
        if not row or not row["hashed_password"]:
            raise HTTPException(status_code=401, detail="User not found")
    except Exception:
        raise HTTPException(status_code=500, detail="Server Error")

    if not verify_password(user.password, row["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect password")

    user_id = row["id"]
    token = create_jwt_token({"sub": str(user_id), "username": user.username})
    response = JSONResponse(
        content={
            "access_token": token,
            "token_type": "bearer",
            "message": f"Welcome, {user.username}",
        },
    )
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response


@users_router.post("/get_user/{user_id}", dependencies=[Depends(role_based_rate_limit)])
async def get_user(
    request: Request,
    user_id: int,
    db: asyncpg.Connection = Depends(get_db_connection),
):
    user_repo = UserRepository(db)
    res = await user_repo.get_user_full_info(user_id)
    if not res:
        return JSONResponse(status_code=404, content={"message": "User not found"})
    return UserInfo(**dict(res))


@users_router.post("/get_users", dependencies=[Depends(role_based_rate_limit)])
@PermissionChecker([RoleEnum.ADMIN, RoleEnum.MODERATOR])
async def get_users(
    request: Request,
    current_user: UserRole = Depends(get_current_user_with_roles),
    db: asyncpg.Connection = Depends(get_db_connection),
):
    user_repo = UserRepository(db)
    res = await user_repo.get_all_users_full_info()
    if not res:
        return JSONResponse(status_code=404, content={"message": "Users not found"})
    return [UserInfo(**dict(usr)) for usr in res]


@users_router.delete("/delete_user/{user_id}")
@PermissionChecker([RoleEnum.ADMIN])
async def delete_user(
    user_id: int,
    current_user: UserRole = Depends(get_current_user_with_roles),
    db: asyncpg.Connection = Depends(get_db_connection),
):
    user_repo = UserRepository(db)
    success = await user_repo.delete_user_by_id(user_id)
    if not success:
        return JSONResponse(status_code=404, content={"message": "User not found"})

    return {"message": "User and his todos are successfully deleted!"}
