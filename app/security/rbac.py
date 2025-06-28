from functools import wraps

from fastapi import HTTPException, status

from app.models.models import RoleEnum


class PermissionChecker:
    """Декоратор для проверки ролей пользователя"""

    def __init__(self, roles: list[RoleEnum]):
        self.roles = roles  # Список разрешённых ролей

    def __call__(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get("current_user")  # Получаем текущего пользователя
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authentication Required",
                )

            if RoleEnum.ADMIN in user.roles:  # Админ всегда имеет доступ ко всему
                return await func(*args, **kwargs)

            if not any(role in user.roles for role in self.roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permissions to access this resource",
                )
            return await func(*args, **kwargs)

        return wrapper
