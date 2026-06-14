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
from services.ai_chatbot import get_chatbot
from services.sentiment_analysis import get_sentiment_analyzer
from services.report_generator_ai import generate_report as ai_generate_report
from services.insight_generator import generate_insights as ai_generate_insights
from services.recommendation_ai import generate_recommendations as ai_generate_recommendations
from config import HF_PREFERRED_MODEL, HF_FALLBACK_MODEL
from services.analytics_service import export_data


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


@api_v2_bp.post("/chat")
def chat_endpoint():
    """POST /api/v2/chat - body: {"message": "...", "user_id": "..."}

    Responde usando o chatbot AI especializado.
    """

    payload = request.get_json(silent=True) or {}
    message = payload.get("message")
    user_id = payload.get("user_id") or request.remote_addr or "anonymous"
    if not message:
        return jsonify({"error": "Campo 'message' obrigatório."}), 400
    try:
        bot = get_chatbot()
        answer = bot.chat(user_id, message)
        return jsonify({"answer": answer})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@api_v2_bp.post("/sentiment")
def sentiment_endpoint():
    """POST /api/v2/sentiment - body: {"text": "..."}

    Analisa sentimento de um texto e devolve classificação + confiança.
    """

    payload = request.get_json(silent=True) or {}
    text = payload.get("text")
    if not text:
        return jsonify({"error": "Campo 'text' obrigatório."}), 400
    try:
        analyzer = get_sentiment_analyzer()
        res = analyzer.analyze(text)
        return jsonify(res)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@api_v2_bp.post("/sentiment/batch")
def sentiment_batch():
    """Executa análise em lote sobre todas as respostas abertas e grava resultados."""

    try:
        analyzer = get_sentiment_analyzer()
        count = analyzer.batch_analyze_all()
        return jsonify({"processed": count})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@api_v2_bp.get("/sentiment/stats")
def sentiment_stats():
    """Devolve contagens agregadas de `sentiment_results` para dashboards."""

    try:
        db = __import__("database.mongodb", fromlist=["get_db"]).get_db()
        rows = db["sentiment_results"].find()
        counts = {"positive": 0, "neutral": 0, "negative": 0}
        for r in rows:
            s = r.get("sentiment", "neutral")
            if s not in counts:
                counts[s] = 0
            counts[s] += 1
        total = sum(counts.values())
        return jsonify({"counts": counts, "total": total})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@api_v2_bp.get("/export-report/pdf")
def export_report_pdf():
    """Gera um relatório AI e devolve em PDF (requer reportlab)."""

    stats = all_surveys()
    text = ai_generate_report(stats)
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        import io

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        y = height - 50
        for line in text.splitlines():
            c.drawString(40, y, line[:1000])
            y -= 14
            if y < 50:
                c.showPage()
                y = height - 50
        c.save()
        buffer.seek(0)
        return Response(buffer.read(), mimetype="application/pdf", headers={"Content-Disposition": "attachment; filename=report.pdf"})
    except Exception as exc:
        return jsonify({"error": "reportlab não disponível ou falha na geração: " + str(exc)}), 500


@api_v2_bp.get("/export-report/docx")
def export_report_docx():
    """Gera um relatório AI e devolve em DOCX (requer python-docx)."""

    stats = all_surveys()
    text = ai_generate_report(stats)
    try:
        from docx import Document
        import io

        doc = Document()
        for line in text.splitlines():
            doc.add_paragraph(line)
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return Response(buffer.read(), mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers={"Content-Disposition": "attachment; filename=report.docx"})
    except Exception as exc:
        return jsonify({"error": "python-docx não disponível ou falha na geração: " + str(exc)}), 500


@api_v2_bp.get("/ai/insights")
def ai_insights():
    """GET /api/v2/ai/insights devolve Top 5 insights gerados por IA."""

    stats = all_surveys()
    try:
        insights = ai_generate_insights(stats)
        return jsonify({"insights": insights})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@api_v2_bp.get("/recommendations/<user_id>")
def ai_recommendations(user_id: str):
    """GET /api/v2/recommendations/<user_id> gera recomendações personalizadas."""

    # Esta rota espera que exista lógica para obter sinais do utilizador
    # (árvore, rf, cluster, índice de desinformação, sentimento).
    # Aqui fazemos uma recolha simplificada usando serviços existentes.
    surveys = all_surveys()
    user = None
    for s in surveys:
        if str(s.get("user_id")) == str(user_id):
            user = s
            break
    signals = {
        "decision_tree": user.get("decision_tree") if user else "unknown",
        "random_forest": user.get("random_forest") if user else "unknown",
        "cluster": user.get("cluster") if user else "unknown",
        "disinformation_index": user.get("disinformation_index") if user else 0,
        "sentiment": (user.get("sentiment") if user else "neutral"),
    }
    try:
        recs = ai_generate_recommendations(signals)
        return jsonify({"user_id": user_id, "recommendations": recs})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@api_v2_bp.get("/ai/status")
def ai_status():
    """Devolve informações simples sobre a configuração de IA (modelo em uso)."""

    try:
        return jsonify({"preferred_model": HF_PREFERRED_MODEL, "fallback_model": HF_FALLBACK_MODEL})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@api_v2_bp.get("/regions")
def regions_ranking():
    """Devolve lista ordenada de províncias com média de índice de desinformação."""

    try:
        return jsonify(regional_disinformation()["byProvince"])
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@api_v2_bp.get("/regions/<province>/municipalities")
def municipalities_for_province(province: str):
    """Devolve ranking de municípios para uma província específica."""

    try:
        rd = regional_disinformation()
        # filtra municípios pertencentes à província — assumimos naming consistente
        by_mun = rd.get("byMunicipality", [])
        # Quando a coleção não contém associação provincia->municipio explícita,
        # devolvemos todos os municípios e o frontend deve filtrar por seleção local.
        return jsonify(by_mun)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@api_v2_bp.get("/ai/metrics")
def ai_metrics():
    """Agrega métricas de ai_logs: chamadas, erros, tempo medio e modelos usados."""

    try:
        db = __import__("database.mongodb", fromlist=["get_db"]).get_db()
        rows = list(db["ai_logs"].find())
        total = len(rows)
        errors = sum(1 for r in rows if not r.get("success"))
        avg_latency = round(sum(r.get("latency", 0) for r in rows) / total, 3) if total else 0
        model_counts = {}
        for r in rows:
            m = r.get("model") or "unknown"
            model_counts[m] = model_counts.get(m, 0) + 1
        return jsonify({"total_calls": total, "errors": errors, "avg_latency": avg_latency, "models": model_counts})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@api_v2_bp.get("/export-data/csv")
def export_data_csv():
    """Exporta todos os dados anonimizados em CSV para download."""

    try:
        content, mimetype, filename = export_data("csv")
        return Response(content, mimetype=mimetype, headers={"Content-Disposition": f"attachment; filename={filename}"})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


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
