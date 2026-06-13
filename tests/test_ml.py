"""Testes dos algoritmos de Machine Learning e pontuação."""

from ml.clustering import cluster_surveys
from ml.disinformation_score import calculate_disinformation_score
from ml.predictor import predict_risk


def test_disinformation_score_high_risk():
    payload = {
        "age": 17,
        "sourceOfInformation": "Colegas",
        "receivedSexEducation": False,
        "schoolEducation": False,
        "needMoreInformation": True,
        "feelsEmbarrassed": True,
    }
    result = calculate_disinformation_score(payload)
    assert result["score"] == 100
    assert result["category"] == "Alto"


def test_predictor_returns_risk():
    result = predict_risk({
        "age": 18,
        "sourceOfInformation": "Escola",
        "receivedSexEducation": True,
        "schoolEducation": True,
        "needMoreInformation": False,
        "feelsEmbarrassed": False,
    })
    assert result["risk"] in {"Baixo", "Médio", "Alto"}


def test_clustering_returns_summary():
    rows = [
        {"age": 16, "sourceOfInformation": "Colegas", "receivedSexEducation": False, "schoolEducation": False, "needMoreInformation": True, "feelsEmbarrassed": True},
        {"age": 20, "sourceOfInformation": "Escola", "receivedSexEducation": True, "schoolEducation": True, "needMoreInformation": False, "feelsEmbarrassed": False},
    ]
    result = cluster_surveys(rows)
    assert "clusters" in result
