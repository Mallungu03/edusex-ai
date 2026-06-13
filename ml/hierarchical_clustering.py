"""Clusterizacao hierarquica para comparar com K-Means."""

from collections import Counter

import numpy as np
from sklearn.cluster import AgglomerativeClustering

from ml.disinformation_score import calculate_disinformation_score


def hierarchical_clusters(surveys: list[dict]) -> dict:
    """Agrupa respostas por idade, score e indicadores comportamentais."""

    if len(surveys) < 3:
        return {"groups": [], "dendrogram": []}

    features = np.array([
        [
            row.get("age", 0),
            calculate_disinformation_score(row)["score"],
            int(bool(row.get("feelsEmbarrassed"))),
            int(bool(row.get("needMoreInformation"))),
        ]
        for row in surveys
    ])
    cluster_count = min(4, len(surveys))
    model = AgglomerativeClustering(n_clusters=cluster_count)
    labels = model.fit_predict(features)
    counts = Counter(int(label) for label in labels)
    names = ["Perfil A - Bem informado", "Perfil B - Necessita apoio", "Perfil C - Alto risco", "Perfil D - Intervencao prioritaria"]

    groups = [{"name": names[index], "count": counts.get(index, 0)} for index in range(cluster_count)]
    dendrogram = [{"from": names[int(labels[i - 1])], "to": names[int(labels[i])], "distance": int(abs(labels[i] - labels[i - 1]) + 1)} for i in range(1, min(len(labels), 20))]
    return {"groups": groups, "dendrogram": dendrogram}


def risk_profiles(surveys: list[dict]) -> dict:
    """Classifica participantes nos quatro perfis de risco pedidos."""

    profiles = Counter()
    examples = []
    for row in surveys:
        score = calculate_disinformation_score(row)
        if score["score"] <= 25:
            profile = "Perfil A - Bem informado"
        elif score["score"] <= 50:
            profile = "Perfil B - Necessita apoio"
        elif score["score"] <= 75:
            profile = "Perfil C - Alto risco"
        else:
            profile = "Perfil D - Intervencao prioritaria"
        profiles[profile] += 1
        if len(examples) < 25:
            examples.append({"profile": profile, "province": row.get("province"), "age": row.get("age"), "score": score["score"]})
    return {"profiles": [{"name": key, "count": value} for key, value in profiles.items()], "examples": examples}
