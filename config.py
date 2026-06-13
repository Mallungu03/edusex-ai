"""Configuração central da aplicação EduSex AI.

Este ficheiro concentra as variáveis que mudam entre ambientes. Em produção
elas devem vir de variáveis de ambiente; em desenvolvimento usamos valores
seguros para execução local e apresentação académica.
"""

import os
from datetime import timedelta


def _env_or_default(name: str, default: str, allow_default: bool = True) -> str:
    value = os.getenv(name, default)
    if not allow_default and value == default:
        raise RuntimeError(f"A variável de ambiente {name} deve ser definida em produção.")
    return value


class Config:
    """Configuração base usada pelo Flask e pelas extensões."""

    ENVIRONMENT = os.getenv("FLASK_ENV", "development").lower()
    SECRET_KEY = _env_or_default("SECRET_KEY", "dev-secret-change-me", allow_default=(ENVIRONMENT != "production"))
    JWT_SECRET_KEY = _env_or_default("JWT_SECRET_KEY", "dev-jwt-secret-change-me-please-use-32-bytes", allow_default=(ENVIRONMENT != "production"))
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=2)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)

    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/edusex_ai")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "edusex_ai")
    USE_MEMORY_DB = os.getenv("EDUSEX_USE_MEMORY_DB", "false").lower() == "true"

    CSV_MAX_ROWS = int(os.getenv("CSV_MAX_ROWS", "10000"))
    MODEL_PATH = os.getenv("MODEL_PATH", "data/disinformation_model.joblib")


class TestingConfig(Config):
    """Configuração para testes automatizados."""

    TESTING = True
    USE_MEMORY_DB = True
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
