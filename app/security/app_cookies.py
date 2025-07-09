from uuid import uuid4

from fastapi import Response
from itsdangerous import TimestampSigner

sessions = dict()
signer = TimestampSigner(secret_key="very-secret-key")


def generate_cookie(username: str, response: Response):
    user_id = str(uuid4())
    signed = signer.sign(user_id).decode()
    response.set_cookie(
        key="session_token", value=signed, httponly=True, max_age=300, secure=False
    )
    sessions[username] = signed
