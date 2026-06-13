"""Previsao de tendencias futuras com regressao.

O modulo agrega respostas por mes e usa Linear Regression e Random Forest
Regressor para projetar indicadores simples: indice de desinformacao,
necessidade de informacao e tendencia regional.
"""

from __future__ import annotations

from collections import defaultdict

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression

from ml.disinformation_score import calculate_disinformation_score


def predict_trends(surveys: list[dict], months_ahead: int = 3) -> dict:
    """Projeta indicadores para os proximos meses com dois regressores."""

    if len(surveys) < 4:
        return {"models": [], "future": [], "regional": []}

    frame = pd.DataFrame(_monthly_rows(surveys)).sort_values("month")
    frame["index"] = range(len(frame))
    x = frame[["index"]]
    future_x = pd.DataFrame({"index": range(len(frame), len(frame) + months_ahead)})

    outputs = []
    for target in ["misinformationIndex", "needMoreInformation"]:
        for name, model in {
            "Linear Regression": LinearRegression(),
            "Random Forest Regressor": RandomForestRegressor(n_estimators=80, random_state=42),
        }.items():
            model.fit(x, frame[target])
            predictions = [round(float(value), 1) for value in model.predict(future_x)]
            outputs.append({"model": name, "target": target, "predictions": predictions})

    regional = _regional_projection(surveys)
    future = [
        {"period": f"+{position} mes", "misinformationIndex": outputs[0]["predictions"][position - 1], "needMoreInformation": outputs[2]["predictions"][position - 1]}
        for position in range(1, months_ahead + 1)
    ]
    return {"models": outputs, "future": future, "regional": regional}


def _monthly_rows(surveys: list[dict]) -> list[dict]:
    """Agrega respostas por mes para treino dos regressores."""

    grouped = defaultdict(list)
    for row in surveys:
        grouped[str(row.get("created_at"))[:7]].append(row)
    rows = []
    for month, items in grouped.items():
        rows.append({
            "month": month,
            "misinformationIndex": sum(calculate_disinformation_score(item)["score"] for item in items) / len(items),
            "needMoreInformation": sum(1 for item in items if item.get("needMoreInformation")) * 100 / len(items),
        })
    return rows


def _regional_projection(surveys: list[dict]) -> list[dict]:
    """Calcula tendencia regional simples por media atual."""

    grouped = defaultdict(list)
    for row in surveys:
        grouped[row.get("province", "Nao informado")].append(calculate_disinformation_score(row)["score"])
    return sorted(
        [{"province": province, "currentIndex": round(sum(scores) / len(scores), 1), "trend": "subida" if sum(scores) / len(scores) >= 55 else "estavel"} for province, scores in grouped.items()],
        key=lambda item: item["currentIndex"],
        reverse=True,
    )[:10]
