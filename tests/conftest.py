"""Configuração comum dos testes."""

import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from config import TestingConfig


@pytest.fixture()
def client():
    """Cliente Flask isolado com base em memória."""

    app = create_app(TestingConfig)
    return app.test_client()


def register_and_login(client, email="user@example.com"):
    """Ajuda os testes a obter JWT rapidamente como utilizador USER."""

    client.post("/auth/register", json={
        "name": "Test User",
        "email": email,
        "password": "secret123",
    })
    response = client.post("/auth/login", json={"email": email, "password": "secret123"})
    return response.get_json()["access_token"]


def create_user_and_login(client, role="USER", email="user@example.com"):
    """Cria um utilizador direto na base com papel específico para testes."""

    from database.mongodb import get_db
    from models.user import create_user_document
    from services.auth_service import bcrypt

    db = get_db()
    if role not in {"ADMIN", "RESEARCHER", "USER"}:
        role = "USER"

    password_hash = bcrypt.generate_password_hash("secret123").decode("utf-8")
    document = create_user_document("Test User", email, password_hash, role)
    db["users"].insert_one(document)
    response = client.post("/auth/login", json={"email": email, "password": "secret123"})
    return response.get_json()["access_token"]
