"""Modelo User.

O modelo não depende de Flask. Ele prepara documentos limpos para a coleção
users, deixando regras de autenticação no serviço especializado.
"""

from database.mongodb import now_utc


VALID_ROLES = {"ADMIN", "RESEARCHER", "USER"}


def create_user_document(name: str, email: str, password_hash: str, role: str = "USER") -> dict:
    """Cria o documento que será gravado na coleção users."""

    normalized_role = role.upper()
    if normalized_role not in VALID_ROLES:
        normalized_role = "USER"
    return {
        "name": name.strip(),
        "email": email.strip().lower(),
        "password_hash": password_hash,
        "role": normalized_role,
        "created_at": now_utc(),
        "active": True,
    }


def public_user(user: dict | None) -> dict | None:
    """Remove password_hash antes de devolver dados ao frontend."""

    if not user:
        return None
    return {
        "id": str(user.get("_id")),
        "name": user.get("name"),
        "email": user.get("email"),
        "role": user.get("role", "USER"),
        "created_at": str(user.get("created_at")),
        "active": user.get("active", True),
    }
