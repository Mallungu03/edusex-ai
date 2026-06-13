"""Rotas do chatbot educativo."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from services.chatbot_service import answer_question


chatbot_bp = Blueprint("chatbot", __name__, url_prefix="/chatbot")


@chatbot_bp.post("/message")
@jwt_required()
def message():
    """POST /chatbot/message recebe pergunta e devolve resposta educativa."""

    payload = request.get_json() or {}
    return jsonify(answer_question(payload.get("question", "")))
