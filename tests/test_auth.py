"""Testes de autenticação JWT."""


def test_register_login_and_profile(client):
    response = client.post("/auth/register", json={
        "name": "Ana",
        "email": "ana@example.com",
        "password": "secret123",
        "role": "RESEARCHER",
    })
    assert response.status_code == 201

    login = client.post("/auth/login", json={"email": "ana@example.com", "password": "secret123"})
    assert login.status_code == 200
    token = login.get_json()["access_token"]

    profile = client.get("/auth/profile", headers={"Authorization": f"Bearer {token}"})
    assert profile.status_code == 200
    assert profile.get_json()["user"]["role"] == "USER"
