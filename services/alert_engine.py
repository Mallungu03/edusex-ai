"""Motor de alertas inteligentes para gestores publicos e ONGs."""

from collections import defaultdict

from ml.disinformation_score import calculate_disinformation_score


def generate_alerts(surveys: list[dict]) -> list[dict]:
    """Gera alertas por regiao, faixa etaria e sintomas sociais de risco."""

    alerts = []
    by_province = defaultdict(list)
    by_age_band = defaultdict(list)

    for row in surveys:
        score = calculate_disinformation_score(row)["score"]
        by_province[row.get("province", "Nao informado")].append(score)
        age = int(row.get("age", 0) or 0)
        if age <= 18:
            band = "10-18"
        elif age <= 24:
            band = "19-24"
        else:
            band = "25+"
        by_age_band[band].append(score)

    for province, scores in by_province.items():
        average = sum(scores) / len(scores)
        if average >= 70:
            alerts.append({
                "type": "ALERTA DE DESINFORMACAO",
                "severity": "Critico",
                "scope": province,
                "message": f"{province} apresenta indice medio de desinformacao de {average:.1f}.",
            })
        elif average >= 55:
            alerts.append({
                "type": "ATENCAO REGIONAL",
                "severity": "Elevado",
                "scope": province,
                "message": f"{province} aproxima-se do limiar de alto risco ({average:.1f}).",
            })

    for band, scores in by_age_band.items():
        average = sum(scores) / len(scores)
        if len(scores) >= 5 and average >= 60:
            alerts.append({
                "type": "ALERTA DE RISCO ETARIO",
                "severity": "Elevado",
                "scope": band,
                "message": f"Faixa {band} anos concentra risco medio de {average:.1f}.",
            })

    return sorted(alerts, key=lambda item: {"Critico": 0, "Elevado": 1}.get(item["severity"], 2))
