"""Serviço de analytics.

Todas as estatísticas são calculadas a partir de survey_responses, evitando
dados hardcoded no frontend. O dashboard apenas consome estes endpoints.
"""

from collections import Counter, defaultdict
from io import BytesIO, StringIO

import pandas as pd

from config import Config
from database.mongodb import get_db
from ml.clustering import cluster_surveys
from ml.disinformation_score import calculate_disinformation_score
from models.survey import anonymize_survey, create_survey_document, validate_survey_payload


def all_surveys() -> list[dict]:
    """Lê todas as respostas do MongoDB."""

    return list(get_db()["survey_responses"].find({}))


def save_survey(payload: dict, user_id: str | None = None) -> tuple[dict, int]:
    """Valida e persiste uma resposta de inquérito."""

    valid, message = validate_survey_payload(payload)
    if not valid:
        return {"message": message}, 400
    document = create_survey_document(payload, user_id)
    result = get_db()["survey_responses"].insert_one(document)
    return {"message": "Resposta registada.", "id": str(result.inserted_id)}, 201


def import_csv(file_storage) -> tuple[dict, int]:
    """Importa CSV enviado pelo formulário administrativo."""

    try:
        frame = pd.read_csv(file_storage, nrows=Config.CSV_MAX_ROWS)
    except Exception as exc:
        return {"message": f"Não foi possível ler o CSV: {exc}"}, 400

    inserted = []
    errors = []
    for index, row in frame.iterrows():
        payload = row.to_dict()
        valid, message = validate_survey_payload(payload)
        if valid:
            inserted.append(create_survey_document(payload))
        else:
            errors.append({"row": int(index) + 2, "message": message})
    if inserted:
        get_db()["survey_responses"].insert_many(inserted)
    return {"inserted": len(inserted), "errors": errors}, 200


def dashboard_statistics() -> dict:
    """Calcula indicadores, distribuições e séries para Chart.js."""

    surveys = all_surveys()
    total = len(surveys)
    if total == 0:
        return empty_statistics()

    ages = [row["age"] for row in surveys]
    bool_percent = lambda field: round(sum(1 for row in surveys if row.get(field)) * 100 / total, 1)
    gender = Counter(row.get("gender", "Não informado") for row in surveys)
    province = Counter(row.get("province", "Não informado") for row in surveys)
    source = Counter(row.get("sourceOfInformation", "Não informado") for row in surveys)

    scores = [calculate_disinformation_score(row) for row in surveys]
    risk = Counter(score["category"] for score in scores)

    monthly = Counter(str(row.get("created_at"))[:7] for row in surveys)
    return {
        "indicators": {
            "totalParticipants": total,
            "averageAge": round(sum(ages) / total, 1),
            "receivedSexEducation": bool_percent("receivedSexEducation"),
            "needMoreInformation": bool_percent("needMoreInformation"),
            "feelsEmbarrassed": bool_percent("feelsEmbarrassed"),
            "pressuredToHaveSex": bool_percent("pressuredToHaveSex"),
            "contraceptiveUse": bool_percent("contraceptiveUse"),
        },
        "charts": {
            "gender": dict(gender),
            "province": dict(province.most_common(10)),
            "source": dict(source),
            "risk": dict(risk),
            "monthly": dict(sorted(monthly.items())),
        },
        "regional": regional_disinformation(),
        "clusters": cluster_surveys(surveys),
    }


def empty_statistics() -> dict:
    """Resposta padrão quando ainda não há inquéritos."""

    return {
        "indicators": {
            "totalParticipants": 0,
            "averageAge": 0,
            "receivedSexEducation": 0,
            "needMoreInformation": 0,
            "feelsEmbarrassed": 0,
            "pressuredToHaveSex": 0,
            "contraceptiveUse": 0,
        },
        "charts": {"gender": {}, "province": {}, "source": {}, "risk": {}, "monthly": {}},
        "regional": {"byProvince": [], "byMunicipality": []},
        "clusters": {"clusters": [], "summary": {}},
    }


def regional_disinformation() -> dict:
    """Calcula ranking de índice médio por província e município."""

    by_province = defaultdict(list)
    by_municipality = defaultdict(list)
    for row in all_surveys():
        score = calculate_disinformation_score(row)["score"]
        by_province[row.get("province", "Não informado")].append(score)
        by_municipality[row.get("municipality", "Não informado")].append(score)

    def rank(grouped):
        return sorted(
            [{"name": key, "averageScore": round(sum(values) / len(values), 1), "count": len(values)} for key, values in grouped.items()],
            key=lambda item: item["averageScore"],
            reverse=True,
        )

    return {"byProvince": rank(by_province), "byMunicipality": rank(by_municipality)}


def public_statistics() -> dict:
    """Devolve estatísticas agregadas e anonimizadas para API pública."""

    stats = dashboard_statistics()
    stats["sample"] = [anonymize_survey(row) for row in all_surveys()[:25]]
    return stats


def export_data(format_name: str):
    """Exporta dados anonimizados em CSV, JSON ou Excel."""

    rows = [anonymize_survey(row) for row in all_surveys()]
    frame = pd.DataFrame(rows)
    if format_name == "json":
        return frame.to_json(orient="records", force_ascii=False), "application/json", "edusex_export.json"
    if format_name == "excel":
        buffer = BytesIO()
        frame.to_excel(buffer, index=False)
        buffer.seek(0)
        return buffer.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "edusex_export.xlsx"
    buffer = StringIO()
    frame.to_csv(buffer, index=False)
    return buffer.getvalue(), "text/csv", "edusex_export.csv"
