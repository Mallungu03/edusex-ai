"""Rotas de inquéritos e importação CSV."""

from flask import Blueprint, jsonify, request

from services.analytics_service import import_csv, save_survey


survey_bp = Blueprint("survey", __name__, url_prefix="/surveys")


@survey_bp.post("")
def create_survey():
    """POST /surveys recebe formulário do frontend e grava no MongoDB."""

    response, status = save_survey(request.get_json() or {}, None)
    return jsonify(response), status


@survey_bp.post("/upload")
def upload_csv():
    """POST /surveys/upload importa CSV validado para a base."""

    file_storage = request.files.get("file")
    if not file_storage:
        return jsonify({"message": "Envie um ficheiro CSV no campo file."}), 400
    response, status = import_csv(file_storage)
    return jsonify(response), status
