import asyncpg
from asyncpg import UniqueViolationError
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from app.api.schemas.models import (
    RoleEnum,
    UserInfo,
    UserLogin,
    UserRegistration,
    UserRole,
)
from app.database.database import get_db_connection
from app.security.rbac import PermissionChecker, role_based_rate_limit

# from fastapi_babel import Babel, BabelConfigs, BabelMiddleware, _
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
    try:
        user_id = await db.fetchval(
            """
            INSERT INTO users (username, hashed_password)
            VALUES ($1, $2)
            RETURNING id
        """,
            user.username,
            get_password_hash(user.password),
        )
    except UniqueViolationError:
        raise HTTPException(status_code=409, detail="User already exists.")

    await db.execute(
        """
        INSERT INTO user_info (user_id, full_name, email)
        VALUES ($1, $2, $3)
    """,
        user_id,
        user.full_name,
        user.email,
    )

    await db.execute(
        """
            INSERT INTO user_roles (user_id, user_role)
            VALUES ($1, $2)
        """,
        user_id,
        RoleEnum.USER.value,
    )

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
    try:
        row = await db.fetchrow(
            """
        SELECT id, hashed_password 
        FROM users
        WHERE username = $1
        """,
            user.username,
        )
        real_pass = row["hashed_password"]

        if not real_pass:
            raise HTTPException(status_code=401, detail="User not found")
    except:
        raise HTTPException(status_code=500, detail="Server Error")

    if not verify_password(user.password, real_pass):
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
    request: Request, user_id: int, db: asyncpg.Connection = Depends(get_db_connection)
):
    res = await db.fetchrow(
        """
        SELECT *, username 
        FROM user_info
        JOIN users ON users.id = user_info.user_id
        WHERE user_id = $1
    """,
        user_id,
    )
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
    res = await db.fetch(
        """
        SELECT * 
        FROM user_info 
        JOIN users ON users.id = user_info.user_id
    """
    )
    if not res:
        return JSONResponse(status_code=404, content={"message": "Users not found"})
    return [UserInfo(**dict(usr)) for usr in res]


@users_router.delete(
    "/delete_user/{user_id}",
)
@PermissionChecker([RoleEnum.ADMIN])
async def delete_user(
    user_id: int,
    current_user: UserRole = Depends(get_current_user_with_roles),
    db: asyncpg.Connection = Depends(get_db_connection),
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
