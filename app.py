"""Ponto de entrada Flask da plataforma EduSex AI.

Fluxo principal:
Frontend HTML/JS -> APIs Flask -> Serviços -> ML -> MongoDB.
"""

from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template
from flask_jwt_extended import JWTManager

from config import Config
from database.mongodb import get_db, init_db
from models.survey import create_survey_document
from routes.analytics import analytics_bp
from routes.api import api_bp
from routes.api_v2 import api_v2_bp
from routes.auth import auth_bp
from routes.chatbot import chatbot_bp
from routes.ml import ml_bp
from routes.survey import survey_bp
from services.auth_service import init_auth, is_token_revoked


def create_app(config_class=Config):
    """Cria e configura a aplicação Flask."""

    app = Flask(__name__)
    app.config.from_object(config_class)

    init_db(app)
    init_auth(app)
    jwt = JWTManager(app)

    @jwt.token_in_blocklist_loader
    def token_revoked(jwt_header, jwt_payload):
        """Impede uso de tokens revogados por logout."""

        return is_token_revoked(jwt_payload["jti"])

    app.register_blueprint(auth_bp)
    app.register_blueprint(survey_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(ml_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(api_v2_bp)

    register_pages(app)
    seed_demo_data()
    return app


def register_pages(app):
    """Regista páginas HTML que consomem APIs REST reais."""

    @app.get("/")
    def index():
        return render_template("login.html")

    @app.get("/register")
    def register_page():
        return render_template("register.html")

    @app.get("/dashboard")
    def dashboard_page():
        return render_template("dashboard.html")

    @app.get("/analytics-page")
    def analytics_page():
        return render_template("analytics.html")

    @app.get("/chatbot-page")
    def chatbot_page():
        return render_template("chatbot.html")

    @app.get("/admin")
    def admin_page():
        return render_template("admin.html")

    @app.get("/surveys-page")
    def surveys_page():
        return render_template("surveys.html")

    @app.get("/predictions")
    def predictions_page():
        return render_template("predictions.html")

    @app.get("/ai-explanation")
    def ai_explanation_page():
        return render_template("ai_explanation.html")

    @app.get("/heatmap")
    def heatmap_page():
        return render_template("heatmap.html")

    @app.get("/executive-dashboard")
    def executive_dashboard_page():
        return render_template("executive_dashboard.html")

    @app.get("/model-comparison")
    def model_comparison_page():
        return render_template("model_comparison.html")

    @app.get("/ai-dashboard")
    def ai_dashboard_page():
        return render_template("ai_dashboard.html")


def seed_demo_data():
    """Carrega uma amostra inicial se a base estiver vazia."""

    db = get_db()
    if db["survey_responses"].count_documents({}) > 0:
        return
    csv_path = Path("data/sample_dataset.csv")
    if not csv_path.exists():
        return
    try:
        import pandas as pd

        frame = pd.read_csv(csv_path).head(80)
        db["survey_responses"].insert_many([create_survey_document(row.to_dict()) for _, row in frame.iterrows()])
    except Exception:
        return


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
