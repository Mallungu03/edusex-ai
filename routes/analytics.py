"""Rotas de analytics protegidas por JWT."""

from flask import Blueprint, jsonify

from ml.hierarchical_clustering import hierarchical_clusters, risk_profiles
from ml.model_comparison import compare_models
from ml.trend_prediction import predict_trends
from services.alert_engine import generate_alerts
from services.analytics_service import dashboard_statistics, regional_disinformation
from services.data_insights import top_insights
from services.analytics_service import all_surveys
from services.explainable_ai import explain_prediction
from services.myth_detector import detect_myth
from services.recommendation_engine import recommend_for_user
from services.report_generator import generate_report_text


analytics_bp = Blueprint("analytics", __name__, url_prefix="/analytics")


@analytics_bp.get("/dashboard")
def dashboard():
    """GET /analytics/dashboard alimenta cards e gráficos Chart.js."""

    return jsonify(dashboard_statistics())


@analytics_bp.get("/regions")
def regions():
    """GET /analytics/regions devolve ranking regional de desinformação."""

    return jsonify(regional_disinformation())


@analytics_bp.get("/insights")
def insights():
    """GET /analytics/insights alimenta resumo automatico dos dados."""

    return jsonify(top_insights(all_surveys()))


@analytics_bp.get("/trends")
def trends():
    """GET /analytics/trends alimenta previsoes futuras."""

    return jsonify(predict_trends(all_surveys()))


@analytics_bp.get("/alerts")
def alerts():
    """GET /analytics/alerts alimenta centro de alertas."""

    return jsonify(generate_alerts(all_surveys()))


@analytics_bp.get("/model-comparison")
def model_comparison():
    """GET /analytics/model-comparison compara modelos para a UI."""

    return jsonify(compare_models())


@analytics_bp.get("/hierarchical-clusters")
def hierarchical():
    """GET /analytics/hierarchical-clusters compara clusterizacao."""

    return jsonify(hierarchical_clusters(all_surveys()))


@analytics_bp.get("/risk-profiles")
def profiles():
    """GET /analytics/risk-profiles devolve perfis A-D."""

    return jsonify(risk_profiles(all_surveys()))


@analytics_bp.post("/myth-detector")
def myth_detector():
    """POST /analytics/myth-detector classifica mito ou verdade."""

    from flask import request

    return jsonify(detect_myth((request.get_json() or {}).get("statement", "")))


@analytics_bp.post("/recommendations")
def recommendations():
    """POST /analytics/recommendations devolve recomendacoes personalizadas."""

    from flask import request

    return jsonify(recommend_for_user(request.get_json() or {}))


@analytics_bp.get("/report-text")
def report_text():
    """GET /analytics/report-text devolve relatorio automatico em texto."""

    return jsonify({"report": generate_report_text(all_surveys())})


@analytics_bp.post("/explain")
def explain():
    """POST /analytics/explain devolve predicao explicavel."""

    from flask import request

    return jsonify(explain_prediction(request.get_json() or {}))
