"""Rotas do chatbot educativo."""

from flask import Blueprint, jsonify, request

from services.chatbot_service import answer_question


chatbot_bp = Blueprint("chatbot", __name__, url_prefix="/chatbot")


@chatbot_bp.post("/message")
def message():
    """POST /chatbot/message recebe pergunta e devolve resposta educativa."""

    payload = request.get_json() or {}
    return jsonify(answer_question(payload.get("question", "")))
