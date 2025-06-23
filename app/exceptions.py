from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from typing import Union

class CustomException(HTTPException):
    def __init__(self, detail: str, status_code: int, message: str):
        super().__init__(status_code=status_code, detail=detail)
        self.message = message

