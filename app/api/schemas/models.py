import re
from datetime import datetime
from enum import Enum
from typing import Optional

from fastapi import HTTPException
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

language_pattern = re.compile(
    r"(?i:(?:\*|[a-z\-]{2,5})(?:;q=\d\.\d)?,)+(?:\*|[a-z\-]{2,5})(?:;q=\d\.\d)?"
)
version_pattern = re.compile(r"\d+\.\d+\.\d+")

MINIMUM_APP_VERSION = "0.0.2"


class CommonHeaders(BaseModel):
    user_agent: str = Field(alias="user-agent")
    accept_language: str = Field(alias="accept-language")
    x_current_version: str = Field(alias="x-current-version")

    @field_validator("accept_language")
    def validate_language(cls, accept_language):
        if language_pattern.match(accept_language) is None:
            raise HTTPException(
                status_code=422, detail="Invalid Accept-Language header"
            )
        return accept_language

    @field_validator("x_current_version", mode="before")
    def validate_version(cls, x_current_version):
        if version_pattern.match(x_current_version) is None:
            raise HTTPException(
                status_code=422, detail="Invalid X-Current-Version header"
            )

        curr_version = [int(i) for i in x_current_version.split(".")]
        min_version = [int(i) for i in MINIMUM_APP_VERSION.split(".")]
        if curr_version < min_version:
            raise HTTPException(
                status_code=422, detail="Version is too old, please update"
            )

        return x_current_version

    @model_validator(mode="before")
    @classmethod
    def check_missing_fields(cls, data):
        required_fields = {"user-agent", "accept-language", "x-current-version"}
        missing_fields = required_fields - set(data.keys())
        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required headers: {', '.join(missing_fields)}",
            )
        return data


class Contact(BaseModel):
    email: EmailStr
    phone: Optional[int] = None

    @field_validator("phone")
    def validate_phone(cls, value):
        if value is None:
            return value

        phone_str = str(value)
        if not phone_str.isdigit():
            raise ValueError("Номер телефона должен содержать только цифры")
        if not (7 <= len(phone_str) <= 15):
            raise ValueError("Длина номера телефона должна быть от 7 до 15 цифр")
        return value


class UserBase(BaseModel):
    username: str


class UserRegistration(UserBase):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: str


class UserPass(UserBase):
    """Model for authentication"""

    id: int
    hashed_password: str


class UserInfo(UserBase):
    user_id: int
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None


class UserLogin(BaseModel):
    """Model for logging in the system"""

    username: str
    password: str


class RoleEnum(str, Enum):
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"
    GUEST = "guest"


class UserRole(BaseModel):
    """User model with access roles"""

    user_id: int
    disabled: bool = False
    roles: list[RoleEnum]


class Todo(BaseModel):
    title: str = ""
    description: str = ""


class TodoReturn(Todo):
    id: int
    user_id: int
    completed: bool = False
    created_at: datetime = datetime.now()
    completed_at: datetime | None = None


class CustomExceptionModel(BaseModel):
    status_code: int
    er_message: str
    er_details: str
