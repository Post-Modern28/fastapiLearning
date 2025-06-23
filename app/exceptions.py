from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse


class CustomException(HTTPException):
    def __init__(self, detail: str, status_code: int = 400):
        super().__init__(status_code=status_code, detail=detail)
