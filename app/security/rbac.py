import inspect
from functools import wraps

from fastapi import HTTPException, status

from app.database.database import get_note_owner
from app.models.models import RoleEnum, UserRole


class PermissionChecker:
    """Decorator for role-based access check"""

    def __init__(self, roles: list[RoleEnum]):
        self.roles = roles  # List of allowed roles

    def __call__(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get(
                "current_user"
            )  # Get current user (api route function parameter)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authentication Required",
                )

            if RoleEnum.ADMIN in user.roles:  # Admin has access to everything
                return await func(*args, **kwargs)

            if not any(role in user.roles for role in self.roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permissions to access this resource",
                )
            return await func(*args, **kwargs)

        return wrapper


class OwnershipChecker:
    def __call__(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            sig = inspect.signature(func)
            bound = sig.bind_partial(*args, **kwargs)
            bound.apply_defaults()
            arguments = bound.arguments

            user: UserRole = arguments.get("current_user")
            note_id = arguments.get("note_id")
            db = arguments.get("db")

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authentication Required",
                )

            if RoleEnum.ADMIN in user.roles:
                return await func(*args, **kwargs)

            # if isinstance(note_id, int):
            #     note_ids = [note_id]

            owner = await get_note_owner(note_id, db)
            if owner != user.user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permissions to access this resource",
                )

            return await func(*args, **kwargs)

        return wrapper
