import os
import secrets
from typing import List

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from passlib.context import CryptContext

from app.config import load_config
from app.models.models import User, UserInDB

# === CONFIG & INIT ===

config = load_config()
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
security = HTTPBasic()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DOCS_USER = os.getenv("DOCS_USER")
DOCS_PASSWORD = os.getenv("DOCS_PASSWORD")

USER_DATA: List[UserInDB] = []


# === AUTH ===


def docs_auth(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, DOCS_USER)
    correct_password = secrets.compare_digest(credentials.password, DOCS_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication",
            headers={"WWW-Authenticate": "Basic"},
        )


@app.get("/docs", include_in_schema=False)
def custom_swagger_ui_html(credentials: HTTPBasicCredentials = Depends(docs_auth)):
    return get_swagger_ui_html(openapi_url="/openapi.json", title="Secure Docs")


@app.get("/openapi.json", include_in_schema=False)
def custom_openapi(credentials: HTTPBasicCredentials = Depends(docs_auth)):
    return JSONResponse(
        get_openapi(title="Secure Docs", version="1.0.0", routes=app.routes)
    )


# === USER UTILS ===


def get_user_from_db(username: str):
    for user in USER_DATA:
        if user.username == username:
            return user
    return None


def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def auth_user_dep(credentials: HTTPBasicCredentials = Depends(security)):
    for user in USER_DATA:
        if secrets.compare_digest(
            credentials.username.encode("utf-8"), user.username.encode("utf-8")
        ) and verify_password(credentials.password, user.hashed_password):
            return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Basic"},
    )


# === ROUTES ===


@app.post(
    "/register",
    responses={
        200: {"description": "Успешная регистрация"},
        409: {
            "description": "Пользователь уже существует",
            "content": {
                "application/json": {
                    "example": {"message": "User Mike already exists!"}
                }
            },
        },
    },
)
async def register_user(usr: User):
    for user in USER_DATA:
        if secrets.compare_digest(
            usr.username.encode("utf-8"), user.username.encode("utf-8")
        ):
            return JSONResponse(
                status_code=409,
                content={"message": f"User {usr.username} already exists!"},
            )
    USER_DATA.append(
        UserInDB(username=usr.username, hashed_password=get_password_hash(usr.password))
    )
    return JSONResponse(
        status_code=200,
        content={"message": f"User {usr.username} has been successfully registered!"},
    )


@app.get("/login")
async def log_in(user: User = Depends(auth_user_dep)):
    return {"message": f"Welcome, {user.username}!"}


# === RUN ===

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
