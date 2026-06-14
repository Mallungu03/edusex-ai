"""Rotas de autenticação JWT."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt, jwt_required

from services.auth_service import authenticate_user, create_api_key, get_current_user, register_user, revoke_token


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.post("/register")
def register():
    """POST /auth/register cria conta de utilizador."""

    payload = request.get_json() or {}
    response, status = register_user(payload)
    # Se registo bem sucedido, cria tokens e inicia sessao automaticamente.
    if status == 201 and response.get("user"):
        user = response["user"]
        # cria tokens JWT com claims mínimos
        claims = {"role": user["role"], "name": user["name"]}
        access = create_access_token(identity=user["email"], additional_claims=claims)
        refresh = create_refresh_token(identity=user["email"], additional_claims=claims)
        return jsonify({"message": response.get("message"), "user": user, "access_token": access, "refresh_token": refresh}), 201
    return jsonify(response), status


@auth_bp.post("/login")
def login():
    """POST /auth/login devolve access_token e refresh_token."""

    payload = request.get_json() or {}
    user, message = authenticate_user(payload.get("email", ""), payload.get("password", ""))
    if not user:
        return jsonify({"message": message}), 401
    claims = {"role": user["role"], "name": user["name"]}
    return jsonify({
        "message": message,
        "user": user,
        "access_token": create_access_token(identity=user["email"], additional_claims=claims),
        "refresh_token": create_refresh_token(identity=user["email"], additional_claims=claims),
    })


@auth_bp.post("/logout")
@jwt_required()
def logout():
    """POST /auth/logout revoga o token atual em memória."""

    revoke_token(get_jwt()["jti"])
    return jsonify({"message": "Sessão terminada."})


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    """POST /auth/refresh gera novo access_token a partir do refresh_token."""

    user = get_current_user()
    return jsonify({
        "access_token": create_access_token(
            identity=user["email"],
            additional_claims={"role": user["role"], "name": user["name"]},
        )
    })


@auth_bp.get("/profile")
@jwt_required()
def profile():
    """GET /auth/profile devolve o utilizador autenticado."""

    return jsonify({"user": get_current_user()})


@auth_bp.post("/api-keys")
@jwt_required()
def api_keys():
    """POST /auth/api-keys cria API key para o utilizador autenticado."""

    user = get_current_user()
    return jsonify(create_api_key(user["email"])), 201
