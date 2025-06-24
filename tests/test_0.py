import pytest
def test_calculate_sum_error(client):
    try:
        response = client.get("/sum/", params={"a": "invalid", "b": 10})
        response.raise_for_status()
    except Exception as e:
        pytest.fail(f"Тест не прошел: {e}")