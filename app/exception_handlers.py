from fastapi.encoders import jsonable_encoder

from app.models.models import CustomExceptionModel
from exceptions import *

async def custom_exception_handler(request: Request, exc: CustomException) -> JSONResponse:
    error = jsonable_encoder(CustomExceptionModel(status_code=exc.status_code, er_message=exc.message, er_details=exc.detail))
    return JSONResponse(status_code=exc.status_code, content=error)

async def global_exception_handler(_: Request, __: Exception):
    return JSONResponse(
        status_code=421,
        content={"error": "Internal server error"}
    )
