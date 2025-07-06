import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_limiter import FastAPILimiter
from redis.asyncio import Redis

# from fastapi_babel import Babel, BabelConfigs, BabelMiddleware, _
from app.api.routes.notes import todo_router
from app.api.routes.users import users_router
from app.api.schemas.models import (
    RoleEnum,
    UserRole,
)
from app.core.config import load_config
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

templates = Jinja2Templates(directory=TEMPLATES_DIR)

app.include_router(users_router)
app.include_router(todo_router)

# app.add_exception_handler(CustomException, custom_exception_handler)
# app.add_exception_handler(Exception, global_exception_handler)
# app.add_exception_handler(ExpiredTokenException, expired_token_handler)


# ===ROUTES===


@app.get("/", response_class=HTMLResponse)
async def get_login_page(request: Request):
    return templates.TemplateResponse(
        "AuthorizationPage.html",
        {
            "request": request,
            "wrongdata": False,
            "error_message": "",
        },
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
