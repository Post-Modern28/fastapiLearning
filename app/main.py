import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

import asyncpg
import starlette
import uvicorn
from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic
from fastapi.staticfiles import StaticFiles
from fastapi_limiter import FastAPILimiter
from pydantic import ValidationError
from redis.asyncio import Redis

# from fastapi_babel import Babel, BabelConfigs, BabelMiddleware, _
from app.api.routes.notes import todo_router
from app.api.routes.users import users_router
from app.api.schemas.models import (
    RoleEnum,
    UserRole,
)
from app.common.templates import templates
from app.core.config import load_config
from app.core.exception_handlers import (
    custom_request_validation_exception_handler,
    internal_server_error_handler,
    not_found_handler,
    validation_exception_handler,
)
from app.database.database import get_db_connection
from app.database.repositories.user_repository import UserRepository
from app.security.rbac import PermissionChecker, role_based_rate_limit
from app.security.security import (
    get_current_user_with_roles,
)

# import enable_translation

# === CONFIG & INIT ===

config = load_config()
security = HTTPBasic()


DOCS_USER = os.getenv("DOCS_USER")
DOCS_PASSWORD = os.getenv("DOCS_PASSWORD")


logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_: FastAPI):
    redis = Redis(host="localhost", port=6379, decode_responses=True)
    await FastAPILimiter.init(redis)
    yield
    await FastAPILimiter.close()


BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "front"
TEMPLATES_DIR = FRONTEND_DIR / "templates"

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR / "static"), name="static")


app.include_router(users_router)
app.include_router(todo_router)

# app.add_exception_handler(CustomException, custom_exception_handler)
# app.add_exception_handler(Exception, global_exception_handler)
# app.add_exception_handler(ExpiredTokenException, expired_token_handler)
app.add_exception_handler(
    RequestValidationError, custom_request_validation_exception_handler
)
app.add_exception_handler(ValidationError, validation_exception_handler)
app.add_exception_handler(starlette.exceptions.HTTPException, not_found_handler)
app.add_exception_handler(Exception, internal_server_error_handler)


# ===ROUTES===


@app.get("/", response_class=HTMLResponse)
async def get_login_page(request: Request):
    created = request.query_params.get("created") == "true"
    return templates.TemplateResponse(
        "AuthorizationPage.html",
        {"request": request, "error": "", "created": created},
    )


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    current_user: UserRole = Depends(get_current_user_with_roles),
    db: asyncpg.Connection = Depends(get_db_connection),
):
    user_repo = UserRepository(db)
    user_info = await user_repo.get_user_full_info(current_user.user_id)
    return templates.TemplateResponse(
        "Dashboard.html",
        {"request": request, "user": current_user, "user_profile": user_info},
    )


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
