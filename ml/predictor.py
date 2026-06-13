"""Preditor de risco de desinformação.

Usa DecisionTreeClassifier quando scikit-learn está disponível. Caso o modelo
treinado ainda não exista, recorre ao algoritmo explicável de pontuação para
manter a API funcional.
"""

from __future__ import annotations

from pathlib import Path

try:
    import joblib
except Exception:  # pragma: no cover
    joblib = None

from models.survey import to_bool
from ml.disinformation_score import calculate_disinformation_score, recommendations_for_score


FEATURES = [
    "age",
    "sourceOfInformation",
    "receivedSexEducation",
    "feelsEmbarrassed",
    "needMoreInformation",
]


def predict_risk(payload: dict, model_path: str = "data/disinformation_model.joblib") -> dict:
    """Prediz o risco usando modelo treinado ou regra explicável de fallback."""

    score = calculate_disinformation_score(payload)
    if joblib and Path(model_path).exists():
        import pandas as pd

        bundle = joblib.load(model_path)
        pipeline = bundle["pipeline"]
        row = pd.DataFrame([{
            "age": int(payload.get("age", 0) or 0),
            "sourceOfInformation": str(payload.get("sourceOfInformation", "")),
            "receivedSexEducation": to_bool(payload.get("receivedSexEducation", False)),
            "feelsEmbarrassed": to_bool(payload.get("feelsEmbarrassed", False)),
            "needMoreInformation": to_bool(payload.get("needMoreInformation", False)),
        }])
        prediction = pipeline.predict(row)[0]
        score["category"] = prediction
    return {"risk": score["category"], "score": score, "recommendations": recommendations_for_score(score)}
