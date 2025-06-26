import pytest


@pytest.mark.parametrize(
    "a, b, expected_status, expected_result",
    [
        (5, 10, 200, 15),
        (-8, -3, 200, -11),
        (0, 7, 200, 7),
        ("a", 10, 422, None),  # Ошибка валидации: строка вместо числа
        (3, None, 422, None)   # Отсутствует параметр b
    ]
)
def test_calculate_sum_params(a, b, expected_status, expected_result, client):
    params = {"a": a}
    if b is not None:
        params["b"] = b

    response = client.get("/sum/", params=params)
    assert response.status_code == expected_status
    if expected_status == 200:
        assert response.json() == {"result": expected_result}