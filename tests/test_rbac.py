"""Testes de controlo de acesso baseado em papéis."""

from tests.conftest import create_user_and_login, register_and_login


def test_user_cannot_upload_csv(client):
    token = register_and_login(client, email="user@example.com")
    response = client.post("/surveys/upload", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_admin_can_request_training_endpoint(client):
    token = create_user_and_login(client, role="ADMIN", email="admin@example.com")
    response = client.post("/ml/train", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code in {200, 500}
