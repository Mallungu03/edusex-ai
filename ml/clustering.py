"""Clusterização K-Means para perfis de participantes."""

from collections import Counter

try:
    import numpy as np
    from sklearn.cluster import KMeans
except Exception:  # pragma: no cover
    np = None
    KMeans = None

from ml.disinformation_score import calculate_disinformation_score


CLUSTER_NAMES = {
    0: "Bem informados",
    1: "Moderadamente informados",
    2: "Alto risco",
}


def cluster_surveys(surveys: list[dict]) -> dict:
    """Agrupa respostas por idade e índice de desinformação."""

    if not surveys:
        return {"clusters": [], "summary": {}}

    if KMeans is None or np is None or len(surveys) < 3:
        counts = Counter(calculate_disinformation_score(row)["label"] for row in surveys)
        return {"clusters": [{"name": name, "count": count} for name, count in counts.items()], "summary": dict(counts)}

    features = np.array([[row.get("age", 0), calculate_disinformation_score(row)["score"]] for row in surveys])
    model = KMeans(n_clusters=3, random_state=42, n_init=10)
    raw_labels = model.fit_predict(features)

    centers = sorted(
        [(index, center[1]) for index, center in enumerate(model.cluster_centers_)],
        key=lambda item: item[1],
    )
    readable = {cluster_id: CLUSTER_NAMES[position] for position, (cluster_id, _) in enumerate(centers)}

    counts = Counter(readable[int(label)] for label in raw_labels)
    return {
        "clusters": [{"name": name, "count": counts.get(name, 0)} for name in CLUSTER_NAMES.values()],
        "summary": dict(counts),
        "centers": [{"cluster": readable[i], "avg_score": float(model.cluster_centers_[i][1])} for i in readable],
    }
