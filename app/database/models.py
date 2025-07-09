from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    Enum,
    ForeignKey,
    String,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class RoleEnum(str, PyEnum):
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"
    GUEST = "guest"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(128), nullable=False)

    info = relationship(
        "UserInfo", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    roles = relationship(
        "UserRole", back_populates="user", cascade="all, delete-orphan"
    )
    todos = relationship("Todo", back_populates="user", cascade="all, delete-orphan")


class UserInfo(Base):
    __tablename__ = "user_info"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    full_name: Mapped[Optional[str]] = mapped_column(String(100))
    email: Mapped[Optional[str]] = mapped_column(String(100), unique=True)

    user = relationship("User", back_populates="info")


class UserRole(Base):
    __tablename__ = "user_roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    user_role: Mapped[str] = mapped_column(Enum(RoleEnum), nullable=False)
    disabled: Mapped[bool] = mapped_column(default=False)

    user = relationship("User", back_populates="roles")


class Todo(Base):
    __tablename__ = "things_to_do"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(500))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    completed: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    user = relationship("User", back_populates="todos")
