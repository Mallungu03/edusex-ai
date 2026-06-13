"""Motor de recomendacoes personalizadas.

As recomendacoes combinam regras de dominio com sinais gerados pelos modelos:
risco, indice de desinformacao, cluster e perfil. O resultado e explicavel e
adequado para apresentacao academica, pois cada conteudo traz o motivo.
"""

from ml.disinformation_score import calculate_disinformation_score


CONTENT_LIBRARY = {
    "contraceptives": {"title": "Metodos contraceptivos", "priority": "Alta", "format": "Guia pratico"},
    "sti": {"title": "Prevencao de ISTs", "priority": "Alta", "format": "Aula curta"},
    "consent": {"title": "Consentimento e limites", "priority": "Alta", "format": "Modulo interativo"},
    "family": {"title": "Planeamento familiar", "priority": "Media", "format": "Infografico"},
    "trusted_sources": {"title": "Como verificar fontes de informacao", "priority": "Media", "format": "Checklist"},
    "communication": {"title": "Como conversar sem vergonha", "priority": "Media", "format": "Roteiro de conversa"},
    "health_services": {"title": "Quando procurar servicos de saude", "priority": "Alta", "format": "Mapa de apoio"},
    "peer_pressure": {"title": "Pressao social e tomada de decisao", "priority": "Alta", "format": "Estudo de caso"},
}


def recommend_for_user(survey: dict, cluster: str | None = None, ai_result: dict | None = None) -> dict:
    """Gera uma lista priorizada de conteudos para um participante."""

    score = ai_result.get("score") if ai_result else calculate_disinformation_score(survey)
    keys = []
    reasons = {}

    def add(key: str, reason: str):
        if key not in keys:
            keys.append(key)
            reasons[key] = reason

    if score["category"] == "Alto":
        add("contraceptives", "Risco alto exige revisao de metodos preventivos.")
        add("sti", "Risco alto aumenta prioridade de prevencao de ISTs.")
        add("consent", "Apoia decisoes seguras e respeito por limites.")
        add("health_services", "Participantes de alto risco beneficiam de orientacao qualificada.")
    elif score["category"] == "Médio":
        add("trusted_sources", "Risco medio sugere necessidade de verificar informacoes.")
        add("sti", "Reforca conhecimentos preventivos essenciais.")
        add("family", "Ajuda a planear decisoes com informacao.")
    else:
        add("trusted_sources", "Mantem boas praticas de consulta a fontes confiaveis.")
        add("communication", "Estimula partilha responsavel de conhecimento.")

    if not survey.get("contraceptiveUse", False):
        add("contraceptives", "Nao uso de contraceptivos sinaliza lacuna de protecao.")
    if survey.get("feelsEmbarrassed", False):
        add("communication", "Vergonha declarada pode bloquear procura de ajuda.")
    if survey.get("pressuredToHaveSex", False):
        add("peer_pressure", "Pressao social exige intervencao educativa especifica.")
    if str(survey.get("sourceOfInformation", "")).lower() in {"colegas", "amigos", "redes sociais"}:
        add("trusted_sources", "Fonte informal precisa ser validada por evidencias.")
    if cluster and "risco" in cluster.lower():
        add("health_services", "Cluster de risco pede encaminhamento preventivo.")

    items = []
    for position, key in enumerate(keys[:6], start=1):
        content = CONTENT_LIBRARY[key]
        items.append({**content, "rank": position, "reason": reasons[key]})

    return {"risk": score["category"], "misinformationIndex": score["score"], "recommendations": items}


def aggregate_recommendations(surveys: list[dict]) -> list[dict]:
    """Resume os conteudos mais importantes para uma populacao."""

    counts = {}
    for survey in surveys:
        for item in recommend_for_user(survey)["recommendations"]:
            counts[item["title"]] = counts.get(item["title"], 0) + 1
    ranked = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    return [{"title": title, "demand": count} for title, count in ranked[:10]]
