from fastapi import HTTPException
from pydantic import ValidationError


class CustomException(HTTPException):
    def __init__(self, detail: str, status_code: int, message: str):
        super().__init__(status_code=status_code, detail=detail)
        self.message = message


class ExpiredTokenException(HTTPException):
    def __init__(
        self, detail: str = "Session expired", message: str = "Token is expired"
    ):
        super().__init__(status_code=401, detail=detail)
        self.message = message


class InvalidToken(HTTPException):
    def __init__(
        self, detail: str = "Session expired", message: str = "Token is broken"
    ):
        super().__init__(status_code=401, detail=detail)
        self.message = message


class UserRegistrationValidationError(ValidationError):
    pass
