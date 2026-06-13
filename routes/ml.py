"""Rotas de Machine Learning."""

from flask import Blueprint, current_app, jsonify, request

from ml.clustering import cluster_surveys
from ml.predictor import predict_risk
from ml.train_model import train_model
from services.analytics_service import all_surveys
from services.auth_service import admin_required, researcher_required


ml_bp = Blueprint("ml", __name__, url_prefix="/ml")


@ml_bp.post("/predict")
@researcher_required
def predict():
    """POST /ml/predict prediz risco com autenticação JWT."""

    return jsonify(predict_risk(request.get_json() or {}, current_app.config["MODEL_PATH"]))


@ml_bp.post("/train")
@admin_required
def train():
    """POST /ml/train treina DecisionTreeClassifier."""

    return jsonify(train_model(output_path=current_app.config["MODEL_PATH"]))


@ml_bp.get("/clusters")
@researcher_required
def clusters():
    """GET /ml/clusters devolve agrupamentos K-Means."""

    return jsonify(cluster_surveys(all_surveys()))
