"""Gera recomendações personalizadas com base em múltiplos sinais.

Usa um prompt estruturado que incorpora:
- Resultado da Decision Tree
- Resultado da Random Forest
- Cluster do utilizador
- Índice de desinformação
- Sentimento identificado

Devolve uma lista de recomendações curtas e categorizadas por risco.
"""
from __future__ import annotations

from typing import Dict, List

from services.huggingface_service import get_hf_service


def generate_recommendations(signals: Dict) -> Dict[str, List[str]]:
    """Gera recomendações agrupadas por nível de risco.

    `signals` deve conter chaves como 'decision_tree', 'random_forest',
    'cluster', 'disinformation_index', 'sentiment'.
    """

    hf = get_hf_service()
    prompt_lines = [
        "You are an assistant that produces short personalized educational recommendations based on user risk signals.",
        "Signals:",
    ]
    for k, v in signals.items():
        prompt_lines.append(f"- {k}: {v}")
    prompt_lines.append("Return a JSON object with keys 'high_risk', 'medium_risk', 'low_risk' and arrays of 3 concise recommendations each.")
    prompt = "\n".join(prompt_lines)

    out = hf.generate_text(prompt)
    # Tentamos parsear JSON do output; se falhar devolvemos heurística simples.
    try:
        import json

        parsed = json.loads(out)
        return parsed
    except Exception:
        # Heurística curta: devolve recomendações genéricas baseadas em sentimento
        sentiment = signals.get("sentiment", "neutral")
        if sentiment == "negative":
            return {
                "high_risk": ["Procurar apoio em serviços de saúde locais", "Ler materiais sobre métodos contraceptivos", "Falar com um profissional de saúde"],
                "medium_risk": ["Revisar conteúdos básicos sobre ISTs", "Participar em sessões educativas locais", "Consultar recursos de planeamento familiar"],
                "low_risk": ["Explorar conteúdos avançados sobre saúde reprodutiva", "Partilhar informação credível com pares", "Acompanhar novidades em saúde sexual"]
            }
