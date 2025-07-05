from typing import Optional

import asyncpg

from app.api.schemas.models import UserRole, RoleEnum


class UserRepository:
    def __init__(self, db: asyncpg.Connection):
        self.db = db

    async def create_user(self, username: str, hashed_password: str) -> int:
        return await self.db.fetchval(
            """
            INSERT INTO users (username, hashed_password)
            VALUES ($1, $2)
            RETURNING id
            """,
            username, hashed_password
        )

    async def create_user_info(self, user_id: int, full_name: str, email: str):
        await self.db.execute(
            """
            INSERT INTO user_info (user_id, full_name, email)
            VALUES ($1, $2, $3)
            """,
            user_id, full_name, email
        )

    async def get_user_by_username(self, username: str):
        return await self.db.fetchrow(
            """
            SELECT id, hashed_password
            FROM users
            WHERE username = $1
            """,
            username
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