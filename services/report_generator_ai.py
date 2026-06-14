"""Geração de relatórios automáticos com IA.

Este serviço transforma estatísticas agregadas em texto legível e
estruturado usando um modelo LLM via Hugging Face.
"""
from __future__ import annotations

from typing import Dict

from services.huggingface_service import get_hf_service


def generate_report(stats: Dict) -> str:
    """Gera um relatório textual a partir de `stats`.

    O `stats` é um dicionário contendo chaves como 'total_participants',
    'mean_age', 'disinformation_index', 'top_sources', 'clusters' etc.
    """

    hf = get_hf_service()
    prompt_lines = [
        "Você é um especialista em educação sexual. Gere um relatório profissional, curto e claro, com recomendações a partir das estatísticas fornecidas.",
        "Dados:",
    ]
    for k, v in stats.items():
        prompt_lines.append(f"- {k}: {v}")
    prompt_lines.append("Produza um parágrafo de conclusão conciso e 3 recomendações práticas.")
    prompt = "\n".join(prompt_lines)

    # Chama o HF (modelo preferencial configurado no serviço HF)
    return hf.generate_text(prompt)
