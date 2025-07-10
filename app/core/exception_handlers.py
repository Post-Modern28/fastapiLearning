from urllib.parse import urlencode

from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exception_handlers import (
    request_validation_exception_handler as fastapi_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import ValidationError

from app.api.schemas.models import CustomExceptionModel
from app.common.templates import templates
from app.core.exceptions import *


async def custom_exception_handler(
    request: Request, exc: CustomException
) -> JSONResponse:
    error = jsonable_encoder(
        CustomExceptionModel(
            status_code=exc.status_code, er_message=exc.message, er_details=exc.detail
        )
    )
    return JSONResponse(status_code=exc.status_code, content=error)


async def expired_token_handler(request: Request, exc: ExpiredTokenException):
    response = JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "message": exc.message},
    )
    response.delete_cookie("access_token")
    return response


async def global_exception_handler(_: Request, __: Exception):
    return JSONResponse(status_code=500, content={"error": "Internal server error"})


async def value_error_handler(_: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"error": "Manual validation failed", "message": str(exc)},
    )


async def custom_request_validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    if request.url.path == "/users/update_info":
        for error in exc.errors():
            if "email" in error["loc"]:
                query = urlencode({"error": "Invalid email address"})
                break
        else:
            query = urlencode({"error": ""})
        return RedirectResponse(
            url=f"/users/profile?{query}", status_code=status.HTTP_302_FOUND
        )

    if request.url.path == "/users/register":
        for error in exc.errors():
            if "email" in error["loc"]:
                query = urlencode({"error": "Invalid email address"})
                break
        else:
            query = urlencode({"error": ""})
        return RedirectResponse(
            url=f"/users/register?{query}", status_code=status.HTTP_302_FOUND
        )

    # Default behaviour for other routes
    return await fastapi_exception_handler(request, exc)


async def validation_exception_handler(request: Request, exc: ValidationError):
    if request.url.path == "/users/register":
        err_messages = {
            "username": "Username must be 3 to 32 characters long",
            "password": "Password must be at least 3 characters long",
            "email": "Invalid email format",
        }
        errors = []
        for error in exc.errors():
            field = error["loc"][-1]
            msg = err_messages.get(field)
            errors.append(f"{msg}")

        query = urlencode({"error": " \n ".join(errors)})
        return RedirectResponse(
            url=f"/users/register?{query}", status_code=status.HTTP_302_FOUND
        )

    raise exc


async def user_validation_error_handler(
    request: Request, exc: UserRegistrationValidationError
):
    err_messages = {
        "username": "Username must be 3 to 32 characters long",
        "password": "Password must be at least 3 characters long",
        "email": "Invalid email format",
    }

    errors = []
    for error in exc.errors():
        field = error["loc"][-1]
        msg = err_messages.get(field, error["msg"])
        errors.append(msg)

    query = urlencode({"error": " \n ".join(errors)})
    if request.url.path == "/users/register":
        return RedirectResponse(
            url=f"/users/register?{query}", status_code=status.HTTP_302_FOUND
        )
    if request.url.path == "/users/update_info":
        return RedirectResponse(
            url=f"/users/profile?{query}", status_code=status.HTTP_302_FOUND
        )


async def not_found_handler(request: Request, exc: HTTPException):
    print("Got exception:")
    print(exc)
    if exc.status_code == status.HTTP_404_NOT_FOUND:
        return templates.TemplateResponse(
            "Error404.html", {"request": request}, status_code=404
        )
    raise exc


async def internal_server_error_handler(request: Request, exc: Exception):
    print("Internal error:")
    print(exc)
    return templates.TemplateResponse(
        "Error500.html", {"request": request}, status_code=500
    )
