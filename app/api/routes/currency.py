import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.api.schemas.models import (
    RoleEnum,
    Todo,
    TodoReturn,
    UserRole,
)

# from fastapi_babel import Babel, BabelConfigs, BabelMiddleware, _
from app.database.database import get_db_connection
from app.helpers.db_helpers import check_by_id, get_table_columns
from app.security.rbac import OwnershipChecker, PermissionChecker
from app.security.security import (
    get_current_user_with_roles,
)

todo_router = APIRouter(prefix="/currency", tags=["Currency"])

