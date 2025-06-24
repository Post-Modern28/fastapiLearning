from fastapi.testclient import TestClient
from app.main import app  # Предполагается, что объект app объявлен в app/main.py
import pytest

@pytest.fixture
def client():
    return TestClient(app)


