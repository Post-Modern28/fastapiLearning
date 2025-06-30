def test_role_based_access(client):
    # Admin
    login_data = {"username": "admin", "password": "pass"}
    response = client.post("/log_in", json=login_data)
    assert response.status_code == 200
    token = response.json().get("access_token")
    response = client.get("/admin", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == {"message": f"Hello, user 30!"}
    # User: doesn't have access
    login_data = {"username": "badboy", "password": "sokol"}
    response = client.post("/log_in", json=login_data)
    assert response.status_code == 200
    token = response.json().get("access_token")
    response = client.get("/admin", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
