from exceptions import *


async def custom_exception_handler(request: Request, exc: CustomException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})
