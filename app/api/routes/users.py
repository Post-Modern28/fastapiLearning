# app/api/routes/users.py

from urllib.parse import urlencode

import asyncpg
from fastapi import APIRouter, Depends, Form, Query, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import EmailStr, ValidationError

from app.api.schemas.models import (
    RoleEnum,
    UserInfo,
    UserRegistration,
    UserRole, PasswordValidator,
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


@users_router.post(
    "/register", status_code=status.HTTP_201_CREATED
)
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
                "error": "This username already exists",
            },
            status_code=status.HTTP_409_CONFLICT,
        )

    query = urlencode({"created": "true"})
    await user_repo.create_user_info(user_id, user.full_name, user.email)
    await user_repo.assign_default_role(user_id)
    response = RedirectResponse(url=f"/?{query}", status_code=status.HTTP_302_FOUND)

    return response



@users_router.get(
    "/change_password", status_code=status.HTTP_200_OK
)
async def change_user_password(
    request: Request,
    current_user: UserRole = Depends(get_current_user_with_roles),
    db: asyncpg.Connection = Depends(get_db_connection),
):
    return templates.TemplateResponse(
        "ChangePasswordPage.html",
        {
            "request": request,
            "user": current_user,
            "error": "",
        },
        status_code=status.HTTP_200_OK,
    )


@users_router.post(
    "/change_password", status_code=status.HTTP_200_OK
)
async def change_user_password(
    request: Request,
    old_password: str = Form(...),
    new_password: str = Form(...),
    current_user: UserRole = Depends(get_current_user_with_roles),
    db: asyncpg.Connection = Depends(get_db_connection),
):

    user_repo = UserRepository(db)

    row = await user_repo.get_user_by_id(current_user.user_id)

    if (
            not row
            or not row["hashed_password"]
            or not verify_password(old_password, row["hashed_password"])
    ):
        return templates.TemplateResponse(
            "ChangePasswordPage.html",
            {
                "request": request,
                "user": current_user,
                "error": "Incorrect old password",
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    try:
        PasswordValidator(password=new_password)
    except ValidationError as e:
        # Better approach: add this to validation_exception_handler
        return templates.TemplateResponse(
            "ChangePasswordPage.html",
            {
                "request": request,
                "user": current_user,
                "error": "New password must be at least 3 characters long",
            },
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    await user_repo.change_password(current_user.user_id, get_password_hash(new_password))
    query = urlencode({"updated": "true"})

    response = RedirectResponse(url=f"/users/profile?{query}", status_code=status.HTTP_302_FOUND)

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
                "error": "Incorrect username or password",
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    user_id = row["id"]
    token = create_jwt_token({"sub": str(user_id), "username": username})

    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response


@users_router.get("/all_users", response_class=HTMLResponse)
@PermissionChecker([RoleEnum.ADMIN, RoleEnum.MODERATOR])
async def get_users(
    request: Request,
    message: str = Query(default=None),
    current_user: UserRole = Depends(get_current_user_with_roles),
    db: asyncpg.Connection = Depends(get_db_connection),
):
    user_repo = UserRepository(db)
    user_info = await user_repo.get_user_full_info(current_user.user_id)
    res = await user_repo.get_all_users_full_info()
    return templates.TemplateResponse(
        "AllUsers.html",
        {
            "request": request,
            "user": current_user,
            "user_profile": user_info,
            "users": res or [],
            "message": message,
        },
    )


@users_router.post("/{user_id}/delete")  # For HTML forms
@users_router.delete("/{user_id}")
@PermissionChecker([RoleEnum.ADMIN])
async def delete_user(
    request: Request,
    user_id: int,
    current_user: UserRole = Depends(get_current_user_with_roles),
    db: asyncpg.Connection = Depends(get_db_connection),
):
    user_repo = UserRepository(db)
    success = await user_repo.delete_user_by_id(user_id)
    if not success:
        query = urlencode({"message": "User not found"})
    else:
        query = urlencode({"message": "User and his todos are successfully deleted!"})
    return RedirectResponse(
        url=f"/users/all_users?{query}", status_code=status.HTTP_302_FOUND
    )


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
            "user": current_user,
            "user_profile": user_info,
            "updated": updated,
            "error": error,
        },
    )


@users_router.post("/update_info", response_class=RedirectResponse)
@users_router.patch("/update_info", response_class=RedirectResponse)
async def update_user(
    full_name: str = Form(...),
    email: EmailStr = Form(...),
    current_user: UserRole = Depends(get_current_user_with_roles),
    db: asyncpg.Connection = Depends(get_db_connection),
):
    user_repo = UserRepository(db)
    try:
        await user_repo.update_user_info(
            current_user.user_id, full_name or None, email or None
        )
        query = urlencode({"updated": "true"})
    except Exception as e:
        print(e)
        query = urlencode({"error": "Internal error"})

    return RedirectResponse(
        url=f"/users/profile?{query}", status_code=status.HTTP_302_FOUND
    )


@users_router.get("/{user_id}", dependencies=[Depends(role_based_rate_limit)])
async def get_user(
    request: Request,
    user_id: int,
    db: asyncpg.Connection = Depends(get_db_connection),
):
    user_repo = UserRepository(db)
    res = await user_repo.get_user_full_info(user_id)
    if not res:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, content={"message": "User not found"}
        )
    return UserInfo(**dict(res))


@users_router.post("/{user_id}/roles/add")
@PermissionChecker([RoleEnum.ADMIN])
async def add_user_role(
    request: Request,
    user_id: int,
    role: str = Form(...),
    current_user: UserRole = Depends(get_current_user_with_roles),
    db: asyncpg.Connection = Depends(get_db_connection),
):
    user_repo = UserRepository(db)
    res = await user_repo.add_user_role(user_id, role)
    if res:
        query = urlencode({"message": "Role was added"})
    else:
        query = urlencode({"message": "Error: couldn't add role"})
    return RedirectResponse(
        url=f"/users/all_users?{query}", status_code=status.HTTP_302_FOUND
    )


@users_router.post("/{user_id}/roles/remove")
@PermissionChecker([RoleEnum.ADMIN])
async def remove_user_role(
    request: Request,
    user_id: int,
    role: str = Form(...),
    current_user: UserRole = Depends(get_current_user_with_roles),
    db: asyncpg.Connection = Depends(get_db_connection),
):
    user_repo = UserRepository(db)
    res = await user_repo.remove_user_role(user_id, role)
    if res:
        query = urlencode({"message": "Role was removed"})
    else:
        query = urlencode({"message": "Error: couldn't remove role"})
    return RedirectResponse(
        url=f"/users/all_users?{query}", status_code=status.HTTP_302_FOUND
    )
