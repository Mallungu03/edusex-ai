"""Serviço central para interação com a Hugging Face.

Responsabilidades:
- Carregar token com segurança (a partir de `config.py`).
- Inicializar o cliente da Hugging Face (InferenceClient).
- Fornecer métodos de geração de texto e embeddings com retry.
- Tratar erros e expor mensagens úteis.

Este módulo evita hardcoding do token e implementa um pequeno mecanismo
de retry/exponential backoff para chamadas externas.
"""
from __future__ import annotations

import logging
import time
from typing import Any

from huggingface_hub import InferenceClient

from config import HF_TOKEN, HF_PREFERRED_MODEL, HF_FALLBACK_MODEL, HF_MAX_RETRIES, HF_REQUEST_TIMEOUT
from database.mongodb import get_db, now_utc

logger = logging.getLogger(__name__)


class HuggingFaceService:
    """Wrapper simples sobre Hugging Face Inference API.

    Usa `InferenceClient` quando `HF_TOKEN` está disponível. Em ambientes
    sem token as chamadas levantam uma exceção clara — isto facilita testes
    com database em memória sem dependência externa.
    """

    def __init__(self, token: str | None = None, default_model: str | None = None):
        self.token = token or HF_TOKEN
        self.default_model = default_model or HF_PREFERRED_MODEL
        if not self.token:
            # Não interrompe automaticamente a aplicação; os serviços devem
            # verificar e decidir se continuam em memória ou falham.
            logger.warning("Hugging Face token não encontrado; chamadas externas ficarão indisponíveis.")
            self.client = None
        else:
            # Inicializa o cliente com o token fornecido.
            self.client = InferenceClient(token=self.token)

    def _call_with_retry(self, fn, *args, **kwargs) -> Any:
        """Executa `fn` com retry simples e backoff exponencial.

        `fn` é uma função que lança exceções em caso de falha. O método aplica
        HF_MAX_RETRIES tentativas e espera 2^i segundos entre tentativas.
        """

        last_exc = None
        start_time = time.time()
        for attempt in range(1, HF_MAX_RETRIES + 1):
            try:
                result = fn(*args, **kwargs)
                # Regista chamada bem sucedida em ai_logs
                try:
                    db = get_db()
                    db["ai_logs"].insert_one({
                        "endpoint": getattr(fn, "__name__", "call"),
                        "attempts": attempt,
                        "success": True,
                        "error": None,
                        "model": self.default_model,
                        "latency": time.time() - start_time,
                        "created_at": now_utc(),
                    })
                except Exception:
                    logger.debug("Não foi possível gravar ai_logs; continuando.")
                return result
            except Exception as exc:  # pylint: disable=broad-except
                last_exc = exc
                wait = 2 ** (attempt - 1)
                logger.warning("Hugging Face call falhou (attempt %s/%s): %s; backoff %ss", attempt, HF_MAX_RETRIES, exc, wait)
                time.sleep(wait)

        # Depois das tentativas, regista falha e relança a última exceção.
        try:
            db = get_db()
            db["ai_logs"].insert_one({
                "endpoint": getattr(fn, "__name__", "call"),
                "attempts": HF_MAX_RETRIES,
                "success": False,
                "error": str(last_exc),
                "model": self.default_model,
                "latency": time.time() - start_time,
                "created_at": now_utc(),
            })
        except Exception:
            logger.debug("Não foi possível gravar ai_logs (failure); continuando.")
        raise last_exc

    def generate_text(self, prompt: str, model: str | None = None, parameters: dict | None = None) -> str:
        """Gera texto a partir de um `prompt` usando o modelo especificado.

        Retorna a string gerada. Em caso de ausência de token, lança exceção.
        """

        if self.client is None:
            raise RuntimeError("Hugging Face client não está inicializado (token ausente).")

        model = model or self.default_model

        def _call():
            # Usamos o endpoint de text generation do InferenceClient.
            # O formato exacto de retorno pode variar; aqui assumimos que a
            # resposta tem uma chave 'generated_text' ou devolve uma string.
            response = self.client.text_generation(model=model, inputs=prompt, parameters=parameters or {}, timeout=HF_REQUEST_TIMEOUT)
            # A API pode retornar uma lista de outputs ou um dicionário.
            if isinstance(response, list) and response:
                out = response[0]
                if isinstance(out, dict) and "generated_text" in out:
                    return out["generated_text"]
                if isinstance(out, str):
                    return out
            if isinstance(response, dict) and "generated_text" in response:
                return response["generated_text"]
            # Fallback: stringificação segura da resposta.
            return str(response)

        return self._call_with_retry(_call)

    def embed_text(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        """Obtém embeddings para uma lista de textos.

        Dependendo do modelo e da disponibilidade do endpoint, a API pode
        devolver formatos diferentes. Esta função normaliza a saída para
        uma lista de vectores.
        """

        if self.client is None:
            raise RuntimeError("Hugging Face client não está inicializado (token ausente).")

        model = model or self.default_model

        def _call():
            response = self.client.embeddings(model=model, input=texts)
            # A resposta típica contém 'embedding' por item.
            if isinstance(response, list):
                embeddings = []
                for item in response:
                    if isinstance(item, dict) and "embedding" in item:
                        embeddings.append(item["embedding"])
                    elif isinstance(item, list):
                        embeddings.append(item)
                return embeddings
            if isinstance(response, dict) and "data" in response:
                return [d.get("embedding") for d in response["data"]]
            return []

        return self._call_with_retry(_call)


# Fábrica única usada pela aplicação para evitar re-inicializações.
_service: HuggingFaceService | None = None


def get_hf_service() -> HuggingFaceService:
    """Devolve uma instância singleton de `HuggingFaceService`.

    Chamadores podem importar esta função e reutilizar a mesma instância.
    """

    global _service
    if _service is None:
        _service = HuggingFaceService()
    return _service
