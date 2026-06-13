"""Algoritmo próprio de índice de desinformação.

A pontuação é explicável: cada condição de risco soma 20 pontos. Isto facilita
apresentações académicas porque estudantes conseguem auditar o motivo da classe.
"""


def calculate_disinformation_score(survey: dict) -> dict:
    """Calcula pontuação 0-100 e categoria textual."""

    score = 0
    reasons = []

    if not survey.get("receivedSexEducation", False):
        score += 20
        reasons.append("Nunca recebeu educação sexual.")
    if str(survey.get("sourceOfInformation", "")).lower() in {"colegas", "amigos", "redes sociais"}:
        score += 20
        reasons.append("Fonte principal de informação pouco estruturada.")
    if survey.get("feelsEmbarrassed", False):
        score += 20
        reasons.append("Sente vergonha ao falar sobre o tema.")
    if survey.get("needMoreInformation", False):
        score += 20
        reasons.append("Declara necessidade de mais informação.")
    if not survey.get("schoolEducation", False):
        score += 20
        reasons.append("Não teve educação sexual na escola.")

    if score <= 30:
        category = "Baixo"
        label = "Bem informado"
    elif score <= 60:
        category = "Médio"
        label = "Moderadamente informado"
    else:
        category = "Alto"
        label = "Alto risco"

    return {"score": score, "category": category, "label": label, "reasons": reasons}


def recommendations_for_score(score_result: dict) -> list[str]:
    """Gera recomendações educativas simples a partir do risco."""

    if score_result["category"] == "Alto":
        return [
            "Rever conteúdos sobre consentimento e comunicação saudável.",
            "Estudar métodos contraceptivos com fontes oficiais de saúde.",
            "Procurar orientação numa escola, unidade de saúde ou organização confiável.",
        ]
    if score_result["category"] == "Médio":
        return [
            "Comparar informações recebidas com fontes oficiais.",
            "Aprender sinais de ISTs e formas de prevenção.",
        ]
    return ["Continuar a consultar fontes confiáveis e partilhar conhecimento responsável."]
