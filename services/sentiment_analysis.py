"""Análise de sentimentos usando `distilbert-base-uncased-finetuned-sst-2-english`.

Fornece uma API simples para analisar textos individuais e uma função em
lote que processa respostas existentes e persiste os resultados em MongoDB
na coleção `sentiment_results`.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict

import torch
from transformers import pipeline

from database.mongodb import get_db, now_utc

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """Classe que encapsula o classificador de sentimento.

    Usa um pipeline local com o modelo DistilBERT afim.
    """

    def __init__(self):
        device = 0 if torch.cuda.is_available() else -1
        # Inicializa o pipeline; isto descarrega pesos para o sistema local.
        self.pipe = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english", device=device)

    def analyze(self, text: str) -> Dict[str, float]:
        """Analisa um único texto e devolve sentimento + confiança.

        Como o modelo base devolve apenas `POSITIVE` ou `NEGATIVE`, usamos
        um limiar simples para caracterizar `neutral` quando a confiança
        é baixa (< 0.6).
        """

        results = self.pipe(text[:512])  # limita tamanho para evitar loads excessivos
        if not results:
            return {"sentiment": "neutral", "confidence": 0.0}
        res = results[0]
        label = res.get("label", "NEUTRAL").lower()
        score = float(res.get("score", 0.0))
        if score < 0.6:
            sentiment = "neutral"
        else:
            sentiment = "positive" if "positive" in label else "negative"
        return {"sentiment": sentiment, "confidence": round(score, 4)}

    def batch_analyze_all(self) -> int:
        """Analisa em lote todas as respostas abertas (`survey_responses`) e
        grava os resultados na coleção `sentiment_results`.

        Retorna o número de documentos processados.
        """

        db = get_db()
        surveys = db["survey_responses"].find()
        results = []
        for s in surveys:
            text = s.get("open_answer") or s.get("response_text") or ""
            if not text:
                continue
            ana = self.analyze(text)
            results.append({
                "text": text,
                "sentiment": ana["sentiment"],
                "confidence": ana["confidence"],
                "created_at": now_utc(),
            })
        if results:
            db["sentiment_results"].insert_many(results)
        return len(results)


# Exporta uma instância pronta a usar
_analyzer: SentimentAnalyzer | None = None


def get_sentiment_analyzer() -> SentimentAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = SentimentAnalyzer()
    return _analyzer
