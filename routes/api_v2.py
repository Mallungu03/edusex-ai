"""API avancada v2 para pesquisadores.

Todos os endpoints exigem X-API-Key valida e usam rate limiting em memoria.
Para producao, o limitador deveria ser movido para Redis ou gateway externo.
"""

from collections import defaultdict, deque
from time import time

from flask import Blueprint, Response, jsonify, request

from ml.hierarchical_clustering import risk_profiles
from ml.model_comparison import compare_models
from ml.trend_prediction import predict_trends
from services.alert_engine import generate_alerts
from services.analytics_service import all_surveys, regional_disinformation
from services.auth_service import api_key_is_valid
from services.data_insights import top_insights
from services.recommendation_engine import recommend_for_user
from services.report_generator import export_report, generate_report_text


api_v2_bp = Blueprint("api_v2", __name__, url_prefix="/api/v2")
RATE_BUCKETS = defaultdict(deque)
RATE_LIMIT = 60
WINDOW_SECONDS = 60


def require_api_key_and_rate_limit():
    """Valida API key e aplica limite de 60 pedidos por minuto."""

    key = request.headers.get("X-API-Key")
    if not api_key_is_valid(key):
        return jsonify({"message": "API key ausente ou invalida."}), 401

    now = time()
    bucket = RATE_BUCKETS[key]
    while bucket and now - bucket[0] > WINDOW_SECONDS:
        bucket.popleft()
    if len(bucket) >= RATE_LIMIT:
        return jsonify({"message": "Limite de pedidos excedido. Tente novamente em instantes."}), 429
    bucket.append(now)
    return None


@api_v2_bp.before_request
def guard_v2():
    """Protege toda a API v2 antes de chamar a rota final."""

    return require_api_key_and_rate_limit()


@api_v2_bp.get("/insights")
def insights():
    """GET /api/v2/insights devolve resumo automatico dos dados."""

    return jsonify(top_insights(all_surveys()))


@api_v2_bp.get("/trends")
def trends():
    """GET /api/v2/trends devolve previsoes futuras."""

    return jsonify(predict_trends(all_surveys()))


@api_v2_bp.get("/alerts")
def alerts():
    """GET /api/v2/alerts devolve alertas inteligentes."""

    return jsonify(generate_alerts(all_surveys()))


@api_v2_bp.route("/recommendations", methods=["GET", "POST"])
def recommendations():
    """GET/POST /api/v2/recommendations devolve recomendacao para um payload opcional."""

    payload = request.get_json(silent=True) or {}
    if not payload:
        payload = {key: request.args.get(key) for key in request.args}
    if not payload:
        surveys = all_surveys()
        payload = surveys[0] if surveys else {}
    return jsonify(recommend_for_user(payload))


@api_v2_bp.post("/generate-report")
def generate_report():
    """POST /api/v2/generate-report gera relatorio e exporta txt/pdf/docx."""

    format_name = (request.get_json(silent=True) or {}).get("format", "txt")
    text = generate_report_text(all_surveys())
    content, mimetype, filename = export_report(text, format_name)
    return Response(content, mimetype=mimetype, headers={"Content-Disposition": f"attachment; filename={filename}"})


@api_v2_bp.get("/model-comparison")
def model_comparison():
    """GET /api/v2/model-comparison compara Decision Tree e Random Forest."""

    return jsonify(compare_models())


@api_v2_bp.get("/heatmap")
def heatmap():
    """GET /api/v2/heatmap devolve dados regionais para Leaflet."""

    return jsonify(regional_disinformation())


@api_v2_bp.get("/risk-profiles")
def profiles():
    """GET /api/v2/risk-profiles devolve perfis A-D."""

    return jsonify(risk_profiles(all_surveys()))
