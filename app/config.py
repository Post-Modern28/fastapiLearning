# config.py
from dataclasses import dataclass
from enum import Enum

from environs import Env


class Mode(str, Enum):
    DEV = "DEV"
    PROD = "PROD"


@dataclass
class DatabaseConfig:
    database_url: str


@dataclass
class Config:
    db: DatabaseConfig
    secret_key: str
    debug: bool
    mode: Mode


def load_config(path: str = None) -> Config:
    env = Env()
    env.read_env(path)  # Загружаем переменные окружения из файла .env

    return Config(
        db=DatabaseConfig(database_url=env("DATABASE_URL")),
        secret_key=env("SECRET_KEY"),
        debug=env.bool("DEBUG", default=False),
        mode=Mode(env("MODE")),
    )
