"""Serviço de autenticação e autorização.

As rotas chamam estas funções para manter o código HTTP separado das regras de
negócio: criação de utilizador, login, API keys e decorators RBAC.
"""

from functools import wraps
from secrets import token_urlsafe

from flask import jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request

from database.mongodb import get_db, now_utc
from models.user import create_user_document, public_user


bcrypt = Bcrypt()
BLOCKLIST = set()


def init_auth(app):
    """Inicializa bcrypt com a app Flask."""

    bcrypt.init_app(app)


def register_user(payload: dict) -> tuple[dict, int]:
    """Regista um utilizador com password encriptada.

    O registo público ignora qualquer papel passado no payload para evitar a
    elevação de privilégios. Todos os novos utilizadores são criados como USER.
    """

    db = get_db()
    name = str(payload.get("name", "")).strip()
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))

    if not name or not email or not password:
        return {"message": "Nome, email e password são obrigatórios."}, 400
    if db["users"].find_one({"email": email}):
        return {"message": "Email já registado."}, 409

    password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
    document = create_user_document(name, email, password_hash)
    result = db["users"].insert_one(document)
    document["_id"] = result.inserted_id
    return {"message": "Utilizador registado.", "user": public_user(document)}, 201


def authenticate_user(email: str, password: str) -> tuple[dict | None, str]:
    """Valida credenciais e devolve o utilizador público."""

    normalized_email = str(email or "").strip().lower()
    if not normalized_email or not password:
        return None, "Credenciais inválidas."

    user = get_db()["users"].find_one({"email": normalized_email, "active": {"$ne": False}})
    if not user or not bcrypt.check_password_hash(user["password_hash"], password):
        return None, "Credenciais inválidas."
    return public_user(user), "Login efetuado."


def get_current_user() -> dict | None:
    """Obtém o utilizador autenticado a partir do JWT."""

    identity = get_jwt_identity()
    if not identity:
        return None
    return public_user(get_db()["users"].find_one({"email": identity}))


def role_required(*roles):
    """Decorator genérico para RBAC por papéis."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") not in roles:
                return jsonify({"message": "Permissão insuficiente."}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator


admin_required = role_required("ADMIN")
researcher_required = role_required("ADMIN", "RESEARCHER")


def create_api_key(owner: str) -> dict:
    """Cria chave pública para investigadores consumirem APIs anonimizadas."""

    key = token_urlsafe(32)
    document = {"key": key, "owner": owner, "created_at": now_utc(), "active": True}
    get_db()["api_keys"].insert_one(document)
    return {"key": key, "owner": owner}


def api_key_is_valid(key: str | None) -> bool:
    """Verifica se uma API key está ativa."""

    if not key:
        return False
    return get_db()["api_keys"].find_one({"key": key, "active": True}) is not None


def is_token_revoked(jti: str) -> bool:
    """Verifica se um JWT foi revogado.

    Usamos uma coleção persistente para evitar que o logout seja válido apenas
    enquanto o processo estiver ativo.
    """

    if jti in BLOCKLIST:
        return True
    return get_db()["jwt_blocklist"].find_one({"jti": jti}) is not None


def revoke_token(jti: str):
    """Marca um JWT como revogado durante a vida do processo."""

    try:
        get_db()["jwt_blocklist"].insert_one({"jti": jti, "revoked_at": now_utc()})
    except Exception:
        pass
    BLOCKLIST.add(jti)
