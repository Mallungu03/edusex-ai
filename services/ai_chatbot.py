"""Chatbot AI especializado em educação sexual.

Funcionalidades principais:
- Responder apenas a perguntas dentro do domínio definido.
- Utilizar modelo Llama-3 (ou Mistral) via `HuggingFaceService`.
- Guardar histórico de conversa (últimas 5 mensagens) na colecção
  `chat_history` do MongoDB.

O sistema usa uma verificação simples de palavras-chave para identificar
se a pergunta está dentro do domínio; isto evita respostas fora do tema.
Para cenários de produção pode substituir-se por um classificador mais
sofisticado.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import List

from database.mongodb import get_db, now_utc
from services.huggingface_service import get_hf_service
from config import HF_PREFERRED_MODEL, HF_FALLBACK_MODEL

logger = logging.getLogger(__name__)


ALLOWED_TOPICS = [
    "educação sexual",
    "saúde sexual",
    "planeamento familiar",
    "prevenção",
    "IST",
    "puberdade",
    "gravidez",
    "contraceptivos",
    "consentimento",
]

DEFAULT_OUT_OF_DOMAIN_REPLY = "Fui desenvolvido apenas para responder questões relacionadas com educação sexual."


class AIChatbot:
    """Classe que encapsula a lógica do chatbot especializado.

    Guarda o histórico de conversa por `user_id` e limita a memória a 5
    mensagens para cada utilizador.
    """

    def __init__(self, hf_service=None):
        self.hf = hf_service or get_hf_service()
        self.db = get_db()

    def _is_in_domain(self, text: str) -> bool:
        """Verificação simples por palavras-chave para garantir domínio.

        Esta função procura termos chave na pergunta. É intencionalmente
        permissiva e serve de primeira linha de defesa.
        """

        lowered = text.lower()
        for kw in ALLOWED_TOPICS:
            if kw in lowered:
                return True
        return False

    def _append_history(self, user_id: str, role: str, text: str) -> None:
        """Acrescenta uma entrada ao histórico do utilizador e mantém apenas
        as últimas 5 mensagens.
        """

        coll = self.db["chat_history"]
        record = coll.find_one({"user_id": user_id})
        entry = {"role": role, "text": text, "created_at": now_utc()}
        if not record:
            coll.insert_one({"user_id": user_id, "messages": [entry]})
            return
        messages = record.get("messages", [])
        messages.append(entry)
        # Mantém apenas as últimas 5 mensagens
        messages = messages[-5:]
        coll.update_one({"user_id": user_id}, {"$set": {"messages": messages}})

    def _get_history(self, user_id: str) -> List[dict]:
        """Retorna as últimas mensagens do utilizador (máx. 5)."""

        coll = self.db["chat_history"]
        record = coll.find_one({"user_id": user_id})
        return record.get("messages", []) if record else []

    def chat(self, user_id: str, message: str) -> str:
        """Processa uma pergunta do utilizador e devolve uma resposta.

        Passos:
        1. Verifica o domínio; se fora do domínio devolve resposta controlada.
        2. Recolhe o histórico para contexto.
        3. Constrói um prompt seguro e chama o modelo via Hugging Face.
        4. Guarda a pergunta e a resposta no histórico.
        """

        # Verifica domínio
        if not self._is_in_domain(message):
            return DEFAULT_OUT_OF_DOMAIN_REPLY

        # Guarda a pergunta do utilizador
        self._append_history(user_id, "user", message)

        # Monta prompt com histórico para fornecer contexto ao modelo
        history = self._get_history(user_id)
        prompt_parts = ["O seguinte é uma conversa entre um jovem e um assistente informativo sobre educação sexual."]
        for m in history:
            role = m.get("role", "user")
            text = m.get("text", "")
            prompt_parts.append(f"{role}: {text}")
        prompt_parts.append(f"user: {message}")
        prompt_parts.append("assistant:")
        prompt = "\n".join(prompt_parts)

        # Tenta gerar resposta com modelo preferencial e recorre a fallback se necessário
        try:
            resp = self.hf.generate_text(prompt, model=HF_PREFERRED_MODEL)
        except Exception:  # Em caso de falha, tenta fallback e regista erro
            logger.exception("Falha a gerar com modelo preferencial, a tentar fallback.")
            resp = self.hf.generate_text(prompt, model=HF_FALLBACK_MODEL)

        # Guarda a resposta no histórico
        self._append_history(user_id, "assistant", resp)

        return resp


# Fábrica para permitir reutilização simples do chatbot
_chatbot: AIChatbot | None = None


def get_chatbot() -> AIChatbot:
    global _chatbot
    if _chatbot is None:
        _chatbot = AIChatbot()
    return _chatbot
