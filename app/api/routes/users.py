# app/api/routes/users.py

import asyncpg
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import EmailStr, ValidationError

from app.api.schemas.models import (
    RoleEnum,
    UserInfo,
    UserLogin,
    UserRegistration,
    UserRole,
)
from app.common.templates import templates
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


@users_router.get("/register", response_class=HTMLResponse)
async def get_registration_page(request: Request):
    return templates.TemplateResponse(
        "RegistrationPage.html",
        {
            "request": request,
            "error": "",
        },
    )


@users_router.post("/register", response_model=UserInfo, status_code=201)
async def register_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...),
    email: str = Form(...),
    db: asyncpg.Connection = Depends(get_db_connection),
):
    try:
        user = UserRegistration(
            username=username,
            password=password,
            full_name=full_name or None,
            email=email or None,
        )
    except ValidationError as e:
        raise e
    user_repo = UserRepository(db)
    user_id = await user_repo.create_user(
        user.username, get_password_hash(user.password)
    )
    if user_id == -1:
        return templates.TemplateResponse(
            "RegistrationPage.html",
            {
                "request": request,
                "error_message": "This username already exists",
            },
            status_code=409
        )

    query = urlencode({"created": "true"})
    await user_repo.create_user_info(user_id, user.full_name, user.email)
    await user_repo.assign_default_role(user_id)
    response = RedirectResponse(url=f"/?{query}", status_code=302)

    return response


@users_router.post("/log_in")
async def log_in(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: asyncpg.Connection = Depends(get_db_connection),
):
    user_repo = UserRepository(db)

    row = await user_repo.get_user_by_username(username)

    if (
        not row
        or not row["hashed_password"]
        or not verify_password(password, row["hashed_password"])
    ):
        return templates.TemplateResponse(
            "AuthorizationPage.html",
            {
                "request": request,
                "error_message": "Incorrect username or password",
            },
            status_code=401,
        )

    user_id = row["id"]
    token = create_jwt_token({"sub": str(user_id), "username": username})

    response = RedirectResponse(url="/dashboard", status_code=302)
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


@users_router.get("/profile", response_class=HTMLResponse)
async def get_profile(
    request: Request,
    current_user: UserRole = Depends(get_current_user_with_roles),
    db: asyncpg.Connection = Depends(get_db_connection),
):
    user_repo = UserRepository(db)
    user_info = await user_repo.get_user_full_info(current_user.user_id)

    updated = request.query_params.get("updated") == "true"
    error = request.query_params.get("error") or ""

    return templates.TemplateResponse(
        "Profile.html",
        {
            "request": request,
            "user": user_info,
            "updated": updated,
            "error": error,
        },
    )


from urllib.parse import urlencode

@users_router.post("/update_info", response_class=RedirectResponse)
async def update_user(
    full_name: str = Form(...),
    email: EmailStr = Form(...),
    current_user: UserRole = Depends(get_current_user_with_roles),
    db: asyncpg.Connection = Depends(get_db_connection),
):
    # FIX: add email validation
    user_repo = UserRepository(db)
    try:
        await user_repo.update_user_info(current_user.user_id, full_name or None, email or None)
        query = urlencode({"updated": "true"})
    except Exception as e:
        print(e)
        query = urlencode({"error": "Internal error"})

    return RedirectResponse(url=f"/users/profile?{query}", status_code=302)