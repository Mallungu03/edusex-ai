"""Treino do modelo DecisionTreeClassifier.

O rótulo de treino é derivado do índice explicável. Num produto real, estes
rótulos viriam de especialistas; para a apresentação académica, esta estratégia
mantém o dataset auto-contido e auditável.
"""

from pathlib import Path

import pandas as pd
from joblib import dump
from sklearn.compose import ColumnTransformer
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier

from ml.disinformation_score import calculate_disinformation_score


def train_model(csv_path: str = "data/sample_dataset.csv", output_path: str = "data/disinformation_model.joblib") -> dict:
    """Treina, avalia e grava o modelo de classificação."""

    dataset = pd.read_csv(csv_path)
    dataset["risk"] = dataset.apply(lambda row: calculate_disinformation_score(row.to_dict())["category"], axis=1)

    features = dataset[[
        "age",
        "sourceOfInformation",
        "receivedSexEducation",
        "feelsEmbarrassed",
        "needMoreInformation",
    ]]
    labels = dataset["risk"]

    x_train, x_test, y_train, y_test = train_test_split(
        features,
        labels,
        test_size=0.25,
        random_state=42,
        stratify=labels,
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("source", OneHotEncoder(handle_unknown="ignore"), ["sourceOfInformation"]),
            ("numeric", "passthrough", ["age", "receivedSexEducation", "feelsEmbarrassed", "needMoreInformation"]),
        ]
    )
    pipeline = Pipeline([
        ("encoder", preprocessor),
        ("model", DecisionTreeClassifier(max_depth=5, random_state=42)),
    ])
    pipeline.fit(x_train, y_train)

    predictions = pipeline.predict(x_test)
    report = {
        "accuracy": float(accuracy_score(y_test, predictions)),
        "classification_report": classification_report(y_test, predictions, output_dict=True),
    }

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    dump({"pipeline": pipeline}, output_path)
    return report


if __name__ == "__main__":
    print(train_model())
