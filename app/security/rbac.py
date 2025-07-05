import inspect
from functools import wraps

from fastapi import Depends, HTTPException, Request, Response, status
from fastapi_limiter.depends import RateLimiter

from app.api.schemas.models import RoleEnum, UserRole
from app.database.repositories.note_repository import NoteRepository
from app.database.repositories.user_repository import UserRepository
from app.security.security import get_current_user_with_roles


async def role_based_rate_limit(
    request: Request,
    response: Response,
    current_user: UserRole = Depends(get_current_user_with_roles),
) -> RateLimiter:
    if RoleEnum.ADMIN in current_user.roles:
        limiter = RateLimiter(times=10, minutes=1)
    elif RoleEnum.USER in current_user.roles:
        limiter = RateLimiter(times=5, minutes=1)
    else:
        limiter = RateLimiter(times=1, minutes=1)
    await limiter(request=request, response=response)


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

            note_repo = NoteRepository(db)
            owner = await note_repo.get_note_owner(note_id)
            if owner == -1:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Note not found",
                )
            if owner != user.user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permissions to access this resource",
                )

            return await func(*args, **kwargs)

        return wrapper
