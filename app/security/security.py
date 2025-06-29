import datetime
from typing import Optional

import asyncpg
import jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

from app.database.database import get_db_connection
from app.models.models import UserRole, RoleEnum

# Определяем схему аутентификации (OAuth2 с паролем)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Секретный ключ для подписи JWT
# В реальном проекте храните его в .env файле, а не в коде!
SECRET_KEY = "mysecretkey"  # Генерируем через `openssl rand -hex 32`
ALGORITHM = "HS256"  # Используем HMAC SHA-256 для подписи
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # Время жизни токена (15 минут)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_jwt_token(data: dict):
    """Создаём JWT-токен с указанием времени истечения"""
    to_encode = data.copy()
    expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})  # Добавляем время истечения в токен
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_user_from_token(token: str = Depends(oauth2_scheme)):
    """Получаем информацию о пользователе из токена"""
    try:
        payload = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM]
        )  # Декодируем токен
        return payload.get(
            "sub"
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")  # Токен просрочен
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401, detail="Authorization error"
        )


async def get_token_from_header_or_cookie(request: Request) -> Optional[str]:
    # 1. Try to get token from header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[len("Bearer "):]

    # 2. Try to get token from cookie
    token_cookie = request.cookies.get("access_token")
    if token_cookie:
        return token_cookie

    return None

async def get_current_user(token: str = Depends(get_token_from_header_or_cookie)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user_with_roles(
        request: Request,
        db: asyncpg.Connection = Depends(get_db_connection)
) -> UserRole:
    token: Optional[str] = await get_token_from_header_or_cookie(request)

    if token is None:
        return UserRole(user_id=0, roles=[RoleEnum.GUEST])

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        row = await db.fetchrow("""
            SELECT user_id, array_agg(user_role) AS roles
            FROM user_roles
            WHERE disabled = false AND user_id = $1
            GROUP BY user_id
        """, int(user_id))

        if row is None:
            return UserRole(user_id=user_id, roles=[RoleEnum.GUEST])

        roles = [RoleEnum(role) for role in row["roles"]]
        return UserRole(user_id=row["user_id"], roles=roles)

    except jwt.ExpiredSignatureError:
        return UserRole(user_id=0, roles=[RoleEnum.GUEST])
    except jwt.DecodeError:
        return UserRole(user_id=0, roles=[RoleEnum.GUEST])


def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
