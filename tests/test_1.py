def test_calculate_sum(client):
    # Тест 1: валидные входные данные
    response = client.get("/sum/", params={"a": 5, "b": 10})
    assert response.status_code == 200
    assert response.json() == {"result": 15}

    # Тест 2: отрицательные числа
    response = client.get("/sum/", params={"a": -8, "b": -3})
    assert response.status_code == 200
    assert response.json() == {"result": -11}

    # Тест 3: ноль и положительное число
    response = client.get("/sum/", params={"a": 0, "b": 7})
    assert response.status_code == 200
    assert response.json() == {"result": 7}

    # Test case 4: одно число не введено
    response = client.get("/sum/?a=3")
    assert response.status_code == 422  # Unprocessable Entity
    assert response.json() == {
        "detail": [
            {
                "loc": ["query", "b"],
                "msg": "Field required",
                "type": "missing",
                "input": None,
            }
        ]
    }
