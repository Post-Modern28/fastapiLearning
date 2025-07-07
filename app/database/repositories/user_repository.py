# app/database/repositories/user_repository.py
from typing import Optional

import asyncpg
from asyncpg import UniqueViolationError

from app.api.schemas.models import RoleEnum, UserRole


class UserRepository:
    def __init__(self, db: asyncpg.Connection):
        self.db = db

    async def create_user(self, username: str, hashed_password: str) -> int:
        try:
            uid = await self.db.fetchval(
                """
                INSERT INTO users (username, hashed_password)
                VALUES ($1, $2)
                RETURNING id
                """,
                username,
                hashed_password,
            )
            return uid
        except UniqueViolationError:
            return -1

    async def create_user_info(self, user_id: int, full_name: str, email: str):
        await self.db.execute(
            """
            INSERT INTO user_info (user_id, full_name, email)
            VALUES ($1, $2, $3)
            """,
            user_id,
            full_name,
            email,
        )

    async def assign_default_role(self, user_id: int):
        await self.db.execute(
            """
            INSERT INTO user_roles (user_id, user_role)
            VALUES ($1, $2)
            """,
            user_id,
            RoleEnum.USER.value,
        )

    async def get_user_by_username(self, username: str):
        return await self.db.fetchrow(
            """
            SELECT id, hashed_password
            FROM users
            WHERE username = $1
            """,
            username,
        )

    async def get_user_roles_by_id(self, user_id: int) -> Optional[UserRole]:
        row = await self.db.fetchrow(
            """
            SELECT user_id, array_agg(user_role) AS roles
            FROM user_roles
            WHERE disabled = false AND user_id = $1
            GROUP BY user_id
            """,
            user_id,
        )
        if row is None:
            return None
        roles = [RoleEnum(role) for role in row["roles"]]
        return UserRole(user_id=row["user_id"], roles=roles)

    async def get_user_full_info(self, user_id: int):
        return await self.db.fetchrow(
            """
            SELECT *, username 
            FROM user_info
            JOIN users ON users.id = user_info.user_id
            WHERE user_id = $1
            """,
            user_id,
        )

    async def get_all_users_full_info(self):
        return await self.db.fetch(
            """
            SELECT * 
            FROM user_info 
            JOIN users ON users.id = user_info.user_id
            """
        )

    async def delete_user_by_id(self, user_id: int) -> bool:
        result = await self.db.execute(
            """
            DELETE FROM users WHERE id = $1
            """,
            user_id,
        )
        return result != "DELETE 0"

    async def update_user_info(self, user_id: int, full_name: str, email: str) -> bool:
        row = await self.db.fetchrow(
            """
            UPDATE user_info
            SET full_name = $2, email = $3
            WHERE user_id = $1
            RETURNING user_id
            """,
            user_id,
            full_name,
            email
        )
        return row is not None