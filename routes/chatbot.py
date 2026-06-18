"""Rotas do chatbot educativo."""

from flask import Blueprint, jsonify, request

from services.ai_chatbot import get_chatbot


chatbot_bp = Blueprint("chatbot", __name__, url_prefix="/chatbot")


@chatbot_bp.post("/message")
def message():
    """POST /chatbot/message recebe pergunta e devolve resposta educativa."""

    payload = request.get_json() or {}
    question = payload.get("question", "")
    bot = get_chatbot()
    answer = bot.chat(request.remote_addr or "anonymous", question)
    return jsonify({"answer": answer})
