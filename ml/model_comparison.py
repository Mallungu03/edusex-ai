"""Comparacao entre Decision Tree e Random Forest.

O dataset recebe rotulos derivados do indice explicavel de desinformacao. Isso
permite comparar modelos com metricas classicas e escolher automaticamente o
melhor classificador para a apresentacao.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from joblib import dump
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier

from ml.disinformation_score import calculate_disinformation_score


FEATURE_COLUMNS = ["age", "sourceOfInformation", "receivedSexEducation", "feelsEmbarrassed", "needMoreInformation"]


def compare_models(csv_path: str = "data/sample_dataset.csv", output_path: str = "data/best_model.joblib") -> dict:
    """Treina Decision Tree e Random Forest, compara metricas e grava o melhor."""

    dataset = pd.read_csv(csv_path)
    dataset["risk"] = dataset.apply(lambda row: calculate_disinformation_score(row.to_dict())["category"], axis=1)
    x_train, x_test, y_train, y_test = train_test_split(
        dataset[FEATURE_COLUMNS],
        dataset["risk"],
        test_size=0.25,
        random_state=42,
        stratify=dataset["risk"],
    )

    models = {
        "Decision Tree": DecisionTreeClassifier(max_depth=5, random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=120, max_depth=7, random_state=42),
    }
    results = []
    best = None
    for name, estimator in models.items():
        pipeline = _pipeline(estimator)
        pipeline.fit(x_train, y_train)
        predictions = pipeline.predict(x_test)
        metrics = {
            "model": name,
            "accuracy": round(float(accuracy_score(y_test, predictions)), 3),
            "precision": round(float(precision_score(y_test, predictions, average="weighted", zero_division=0)), 3),
            "recall": round(float(recall_score(y_test, predictions, average="weighted", zero_division=0)), 3),
            "f1": round(float(f1_score(y_test, predictions, average="weighted", zero_division=0)), 3),
        }
        results.append(metrics)
        if best is None or metrics["f1"] > best["metrics"]["f1"]:
            best = {"name": name, "metrics": metrics, "pipeline": pipeline}

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    dump({"pipeline": best["pipeline"], "model": best["name"], "metrics": best["metrics"]}, output_path)
    return {"bestModel": best["name"], "metrics": results}


def _pipeline(estimator) -> Pipeline:
    """Cria pipeline comum de pre-processamento categorico e numerico."""

    preprocessor = ColumnTransformer(
        transformers=[
            ("source", OneHotEncoder(handle_unknown="ignore"), ["sourceOfInformation"]),
            ("numeric", "passthrough", ["age", "receivedSexEducation", "feelsEmbarrassed", "needMoreInformation"]),
        ]
    )
    return Pipeline([("encoder", preprocessor), ("model", estimator)])
