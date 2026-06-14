"""Gera insights automáticos a partir de estatísticas.

O serviço devolve os Top 5 insights em formato de lista simples.
"""
from __future__ import annotations

from typing import Dict, List

from services.huggingface_service import get_hf_service


def generate_insights(stats: Dict) -> List[str]:
    """Gera até 5 insights curtos a partir das estatísticas.

    Retorna uma lista de strings com os insights ordenados por importância.
    """

    hf = get_hf_service()
    prompt = (
        "You are an analytics assistant. Given the following statistics, return a numbered Top 5 insights list (one insight per line).\n\n"
        + "Statistics:\n"
        + "\n".join([f"{k}: {v}" for k, v in stats.items()])
        + "\n\nReturn only the numbered insights, 1-5."
    )
    out = hf.generate_text(prompt)
    # O output é texto; devolvemos as linhas não vazias até 5
    lines = [l.strip() for l in out.splitlines() if l.strip()]
    return lines[:5]
