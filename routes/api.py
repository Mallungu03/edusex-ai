"""API pública v1 para investigadores."""

from flask import Blueprint, Response, jsonify, request

from ml.clustering import cluster_surveys
from ml.predictor import predict_risk
from services.analytics_service import all_surveys, dashboard_statistics, export_data, public_statistics, regional_disinformation
from services.auth_service import api_key_is_valid


api_bp = Blueprint("api", __name__, url_prefix="/api/v1")


def require_api_key():
    """Valida chave em X-API-Key para endpoints públicos."""

    if not api_key_is_valid(request.headers.get("X-API-Key")):
        return jsonify({"message": "API key ausente ou inválida."}), 401
    return None


@api_bp.get("/statistics")
def statistics():
    """GET /api/v1/statistics devolve estatísticas anonimizadas."""

    denied = require_api_key()
    if denied:
        return denied
    return jsonify(public_statistics())


@api_bp.get("/indicators")
def indicators():
    """GET /api/v1/indicators devolve indicadores principais."""

    denied = require_api_key()
    if denied:
        return denied
    return jsonify(dashboard_statistics()["indicators"])


@api_bp.get("/regions")
def regions():
    """GET /api/v1/regions devolve ranking regional."""

    denied = require_api_key()
    if denied:
        return denied
    return jsonify(regional_disinformation())


@api_bp.get("/clusters")
def clusters():
    """GET /api/v1/clusters devolve clusters para investigação."""

    denied = require_api_key()
    if denied:
        return denied
    return jsonify(cluster_surveys(all_surveys()))


@api_bp.post("/predict")
def predict():
    """POST /api/v1/predict devolve risco de desinformação."""

    denied = require_api_key()
    if denied:
        return denied
    return jsonify(predict_risk(request.get_json() or {}))


@api_bp.get("/export/<format_name>")
def export(format_name):
    """GET /api/v1/export/csv|json|excel exporta dados anonimizados."""

    denied = require_api_key()
    if denied:
        return denied
    if format_name not in {"csv", "json", "excel"}:
        return jsonify({"message": "Formato inválido."}), 400
    content, mimetype, filename = export_data(format_name)
    return Response(content, mimetype=mimetype, headers={"Content-Disposition": f"attachment; filename={filename}"})
