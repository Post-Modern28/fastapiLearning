import logging
import os
from contextlib import asynccontextmanager

import asyncpg
import uvicorn
from asyncpg import UniqueViolationError
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import HTTPBasic
from fastapi_limiter import FastAPILimiter
from redis.asyncio import Redis

# from fastapi_babel import Babel, BabelConfigs, BabelMiddleware, _
from security.security import get_password_hash

from app.api.routes.notes import todo_router
from app.api.routes.users import users_router
from app.api.schemas.models import (
    RoleEnum,
    UserInfo,
    UserLogin,
    UserRegistration,
    UserRole,
)
from app.config import load_config
from app.database.database import get_db_connection
from app.security.rbac import PermissionChecker, role_based_rate_limit
from app.security.security import (
    create_jwt_token,
    get_current_user_with_roles,
    verify_password,
)

# import enable_translation

# === CONFIG & INIT ===

config = load_config()
security = HTTPBasic()


DOCS_USER = os.getenv("DOCS_USER")
DOCS_PASSWORD = os.getenv("DOCS_PASSWORD")


# Настроим базовый логгер
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_: FastAPI):
    redis = Redis(host="localhost", port=6379, decode_responses=True)
    await FastAPILimiter.init(redis)
    yield
    await FastAPILimiter.close()


app = FastAPI(lifespan=lifespan)
app.include_router(users_router)
app.include_router(todo_router)

# app.add_exception_handler(CustomException, custom_exception_handler)
# app.add_exception_handler(Exception, global_exception_handler)
# app.add_exception_handler(ExpiredTokenException, expired_token_handler)


# ===ROUTES===


@app.get("/")
async def root():
    return RedirectResponse("/docs")


@app.get("/sum/")
def calculate_sum(a: int, b: int):
    return {"result": a + b}


@app.get("/admin")
@PermissionChecker([RoleEnum.ADMIN])
async def admin_info(current_user: UserRole = Depends(get_current_user_with_roles)):
    return {"message": f"Hello, user {current_user.user_id}!"}


@app.get("/public", dependencies=[Depends(role_based_rate_limit)])
async def public_endpoint(
    current_user: UserRole = Depends(get_current_user_with_roles),
):
    return {"message": f"Welcome, your roles: {current_user.roles}"}


# === RUN ===

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
