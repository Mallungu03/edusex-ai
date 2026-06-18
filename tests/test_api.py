"""Testes da API pública com API key."""

from tests.conftest import create_user_and_login


def test_public_api_requires_key(client):
    response = client.get("/api/v2/insights")
    assert response.status_code == 401


def test_public_api_accepts_valid_key(client):
    token = create_user_and_login(client, role="RESEARCHER", email="researcher@example.com")
    key_response = client.post("/auth/api-keys", headers={"Authorization": f"Bearer {token}"})
    key = key_response.get_json()["key"]
    response = client.get("/api/v2/insights", headers={"X-API-Key": key})
    assert response.status_code == 200
    assert "insights" in response.get_json()
