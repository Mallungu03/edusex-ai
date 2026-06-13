"""IA explicavel para previsoes de risco.

Combina tres tecnicas interpretaveis: regras do indice de desinformacao,
importancia manual das variaveis e explicacao textual inspirada na arvore de
decisao. SHAP e indicado como opcional quando a dependencia estiver ausente.
"""

from pathlib import Path

try:
    import joblib
except Exception:  # pragma: no cover
    joblib = None

try:
    import shap
except Exception:  # pragma: no cover
    shap = None

from models.survey import to_bool
from ml.disinformation_score import calculate_disinformation_score
from ml.predictor import predict_risk


FEATURE_IMPORTANCE = {
    "receivedSexEducation": 0.24,
    "sourceOfInformation": 0.22,
    "needMoreInformation": 0.2,
    "feelsEmbarrassed": 0.18,
    "schoolEducation": 0.1,
    "contraceptiveUse": 0.06,
}


def explain_prediction(payload: dict) -> dict:
    """Prediz risco e devolve motivos legiveis por humanos."""

    prediction = predict_risk(payload)
    score = calculate_disinformation_score(payload)
    contributions = []
    feature_names = list(FEATURE_IMPORTANCE.keys())
    for field, importance in FEATURE_IMPORTANCE.items():
        active = _field_increases_risk(field, payload)
        contributions.append({
            "feature": field,
            "importance": importance,
            "impact": round(importance * 100 if active else 0, 1),
            "direction": "aumenta risco" if active else "reduz ou neutraliza risco",
            "explanation": _feature_explanation(field, payload, active),
        })

    shap_info = {
        "available": False,
        "message": "SHAP pode ser integrado quando a dependência shap estiver instalada; esta versão usa importâncias e regras explicáveis.",
        "values": [],
    }
    model_path = Path("data/disinformation_model.joblib")
    if shap and joblib and model_path.exists():
        try:
            bundle = joblib.load(model_path)
            pipeline = bundle["pipeline"]
            import pandas as pd
            row = pd.DataFrame([{
                "age": int(payload.get("age", 0) or 0),
                "sourceOfInformation": str(payload.get("sourceOfInformation", "")),
                "receivedSexEducation": to_bool(payload.get("receivedSexEducation", False)),
                "feelsEmbarrassed": to_bool(payload.get("feelsEmbarrassed", False)),
                "needMoreInformation": to_bool(payload.get("needMoreInformation", False)),
            }])
            explainer = shap.Explainer(pipeline, row)
            shap_values = explainer(row)
            shap_info["available"] = True
            shap_info["message"] = "SHAP foi calculado usando o modelo treinado."
            shap_info["values"] = [
                {
                    "feature": feature_names[index],
                    "value": float(value),
                }
                for index, value in enumerate(shap_values.values[0])
            ]
        except Exception:
            shap_info["available"] = False
            shap_info["message"] = "SHAP não pôde ser calculado com o modelo atual."

    return {
        "result": f"{prediction['risk']} Risco",
        "score": score["score"],
        "reasons": score["reasons"],
        "featureImportance": sorted(contributions, key=lambda item: item["importance"], reverse=True),
        "decisionTreeRules": _tree_rules(payload),
        "shap": shap_info,
    }


def _field_increases_risk(field: str, payload: dict) -> bool:
    """Indica se o valor de uma variavel contribui para risco."""

    if field in {"receivedSexEducation", "schoolEducation", "contraceptiveUse"}:
        return not bool(payload.get(field, False))
    if field in {"needMoreInformation", "feelsEmbarrassed"}:
        return bool(payload.get(field, False))
    if field == "sourceOfInformation":
        return str(payload.get(field, "")).lower() in {"colegas", "amigos", "redes sociais"}
    return False


def _feature_explanation(field: str, payload: dict, active: bool) -> str:
    """Traduz a contribuicao da variavel para linguagem educativa."""

    explanations = {
        "receivedSexEducation": "Nunca recebeu educacao sexual." if active else "Recebeu educacao sexual, reduzindo incerteza.",
        "sourceOfInformation": "Fonte principal pouco estruturada." if active else "Fonte principal mais estruturada ou confiavel.",
        "needMoreInformation": "Declara necessidade de mais informacao." if active else "Nao declarou lacuna informativa imediata.",
        "feelsEmbarrassed": "Demonstra desconforto ao falar do tema." if active else "Nao reporta vergonha como barreira.",
        "schoolEducation": "Nao teve educacao sexual na escola." if active else "Teve apoio educativo escolar.",
        "contraceptiveUse": "Nao usa contraceptivos." if active else "Uso de contraceptivos sinaliza protecao.",
    }
    return explanations[field]


def _tree_rules(payload: dict) -> list[str]:
    """Explicacao baseada nas regras usadas pela Decision Tree simbolica."""

    rules = []
    if not payload.get("receivedSexEducation", False):
        rules.append("Se nao recebeu educacao sexual, adicionar risco estrutural.")
    if str(payload.get("sourceOfInformation", "")).lower() in {"colegas", "amigos", "redes sociais"}:
        rules.append("Se a fonte principal for informal, elevar risco por potencial desinformacao.")
    if payload.get("needMoreInformation", False) and payload.get("feelsEmbarrassed", False):
        rules.append("Se precisa de informacao e sente vergonha, priorizar apoio educativo confidencial.")
    if not rules:
        rules.append("As regras principais nao identificaram sinais fortes de risco.")
    return rules
