from models.models import User

# Фиктивные данные пользователей (в реальном проекте тут будет БД)
USERS_DATA = [
    {
        "username": "admin",
        "password": "adminpass",  # В продакшене пароли должны быть хешированы!
        "roles": ["admin"],
        "full_name": "Admin User",
        "email": "admin@example.com",
        "disabled": False
    },
    {
        "username": "user",
        "password": "userpass",
        "roles": ["user"],
        "full_name": "Regular User",
        "email": "user@example.com",
        "disabled": False
    },
]

def get_user(username: str) -> User:
    """Получаем пользователя по имени (без пароля)"""
    for user_data in USERS_DATA:
        if user_data["username"] == username:
            return User(**{k: v for k, v in user_data.items() if k != "password"})
    return None