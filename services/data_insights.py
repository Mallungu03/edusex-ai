"""Resumo automatico dos dados para analise executiva."""

from collections import Counter

from ml.disinformation_score import calculate_disinformation_score
from services.recommendation_engine import aggregate_recommendations


def sex_education_awareness_score(surveys: list[dict]) -> float:
    """Calcula o indicador nacional 0-100 Sex Education Awareness Score."""

    if not surveys:
        return 0.0
    values = []
    for row in surveys:
        points = 0
        points += 30 if row.get("receivedSexEducation") else 0
        points += 20 if not row.get("needMoreInformation") else 0
        points += 20 if row.get("contraceptiveUse") else 0
        points += 30 if calculate_disinformation_score(row)["score"] <= 40 else 0
        values.append(points)
    return round(sum(values) / len(values), 1)


def top_insights(surveys: list[dict]) -> dict:
    """Gera tendencias, problemas, oportunidades e recomendacoes."""

    if not surveys:
        return {
            "awarenessScore": 0,
            "topInsights": [],
            "topRecommendations": [],
            "trends": [],
            "problems": [],
            "opportunities": [],
        }

    total = len(surveys)
    risks = Counter(calculate_disinformation_score(row)["category"] for row in surveys)
    sources = Counter(row.get("sourceOfInformation", "Nao informado") for row in surveys)
    provinces = Counter(row.get("province", "Nao informado") for row in surveys)
    embarrassment = round(sum(1 for row in surveys if row.get("feelsEmbarrassed")) * 100 / total, 1)
    need_info = round(sum(1 for row in surveys if row.get("needMoreInformation")) * 100 / total, 1)
    no_school = round(sum(1 for row in surveys if not row.get("schoolEducation")) * 100 / total, 1)
    high_risk = round(risks.get("Alto", 0) * 100 / total, 1)
    main_source = sources.most_common(1)[0][0]
    main_province = provinces.most_common(1)[0][0]

    insights = [
        f"{high_risk}% dos participantes estao classificados como alto risco.",
        f"{need_info}% declaram necessidade de mais informacao.",
        f"A fonte de informacao mais frequente e {main_source}.",
        f"{embarrassment}% sentem vergonha ao falar sobre sexualidade.",
        f"A maior concentracao de respostas vem de {main_province}.",
    ]
    problems = [
        f"{no_school}% nao tiveram educacao sexual na escola.",
        f"{embarrassment}% reportam barreira emocional de vergonha.",
        "Fontes informais continuam relevantes na formacao de conhecimento.",
        "Participantes de alto risco exigem acompanhamento prioritario.",
        "Uso irregular de contraceptivos reduz a protecao coletiva.",
    ]
    opportunities = [
        "Criar campanhas por provincia com maior desinformacao.",
        "Reforcar conteudos sobre ISTs, contracepcao e consentimento.",
        "Integrar escolas, familias e unidades de saude.",
        "Usar o chatbot como triagem educativa inicial.",
        "Monitorizar mensalmente o Sex Education Awareness Score.",
    ]
    recommendations = aggregate_recommendations(surveys)[:5]

    return {
        "awarenessScore": sex_education_awareness_score(surveys),
        "topInsights": insights,
        "topRecommendations": recommendations,
        "trends": insights[:3],
        "problems": problems[:5],
        "opportunities": opportunities[:5],
    }
