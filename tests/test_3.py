def test_ownership_access(client):

    # Admin
    login_data = {"username": "admin", "password": "pass"}
    response = client.post("/log_in", json=login_data)
    assert response.status_code == 200
    token = response.json().get("access_token")
    response = client.get("/get_note/23", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()

    # Content owner
    login_data = {"username": "badboy", "password": "sokol"}
    response = client.post("/log_in", json=login_data)
    assert response.status_code == 200
    token = response.json().get("access_token")
    response = client.get("/get_note/23", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    # Neither admin not owner
    login_data = {"username": "danilado", "password": "tennis"}
    response = client.post("/log_in", json=login_data)
    assert response.status_code == 200
    token = response.json().get("access_token")
    response = client.get("/get_note/23", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert response.json() == {"detail": "No access to resource"}
