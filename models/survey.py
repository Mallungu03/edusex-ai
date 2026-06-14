"""Modelo SurveyResponse com validação leve.

Os campos seguem o enunciado do projeto e são usados tanto por formulários
HTML quanto pela importação CSV.
"""

from database.mongodb import now_utc


REQUIRED_FIELDS = [
    "age",
    "gender",
    "province",
    "municipality",
    "receivedSexEducation",
    "who_talked",
    "sourceOfInformation",
    "schoolEducation",
    "parents_main_educators",
    "support_structure",
    "support_structure_location",
    "had_sexual_relations",
    "had_std",
    "std_details",
    "contraceptiveUse",
    "contraceptive_methods",
    "needMoreInformation",
    "pressuredToHaveSex",
    "friends_discuss",
    "feelsEmbarrassed",
]


BOOLEAN_FIELDS = [
    "receivedSexEducation",
    "schoolEducation",
    "parents_main_educators",
    "support_structure",
    "had_sexual_relations",
    "had_std",
    "contraceptiveUse",
    "needMoreInformation",
    "pressuredToHaveSex",
    "friends_discuss",
    "feelsEmbarrassed",
]


def to_bool(value) -> bool:
    """Normaliza valores vindos de JSON, HTML ou CSV para booleanos."""

    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "sim", "yes", "y"}


def validate_survey_payload(payload: dict) -> tuple[bool, str]:
    """Valida campos obrigatórios, tipos e faixa de idade."""

    missing = [field for field in REQUIRED_FIELDS if field not in payload or payload[field] in (None, "")]
    if missing:
        return False, f"Campos obrigatórios ausentes: {', '.join(missing)}"

    try:
        age = int(str(payload["age"]).strip())
    except (TypeError, ValueError):
        return False, "Idade deve ser um número inteiro."
    if age < 10 or age > 80:
        return False, "Idade deve estar entre 10 e 80 anos."

    for field in BOOLEAN_FIELDS:
        value = payload.get(field)
        if value in (None, ""):
            return False, f"Campo booleano ausente: {field}."

    for field in ["gender", "province", "municipality", "sourceOfInformation"]:
        if not str(payload.get(field, "")).strip():
            return False, f"Campo '{field}' deve ser informado."

    return True, "Payload válido."


def create_survey_document(payload: dict, user_id: str | None = None) -> dict:
    """Cria o documento survey_responses já normalizado."""
    document = {
        "age": int(payload["age"]),
        "gender": str(payload["gender"]).strip(),
        "province": str(payload["province"]).strip(),
        "municipality": str(payload["municipality"]).strip(),
        "sourceOfInformation": str(payload.get("sourceOfInformation", "")).strip(),
        "who_talked": str(payload.get("who_talked", "")).strip(),
        "support_structure_location": str(payload.get("support_structure_location", "")).strip(),
        "std_details": str(payload.get("std_details", "")).strip(),
        "contraceptive_methods": payload.get("contraceptive_methods", []),
        "created_at": now_utc(),
    }

    # Normaliza booleanos conhecidos
    for field in BOOLEAN_FIELDS:
        document[field] = to_bool(payload.get(field, False))

    # Campos opcionais adicionais que podem aparecer no payload
    document["parents_main_educators"] = to_bool(payload.get("parents_main_educators", False))
    document["support_structure_location"] = str(payload.get("support_structure_location", "")).strip()
    document["std_details"] = str(payload.get("std_details", "")).strip()
    if user_id:
        document["user_id"] = str(user_id)
    return document


def anonymize_survey(document: dict) -> dict:
    """Remove identificadores antes de exposição pública."""

    clean = dict(document)
    clean.pop("_id", None)
    clean.pop("user_id", None)
    clean.pop("email", None)
    clean.pop("name", None)
    clean["created_at"] = str(clean.get("created_at"))
    return clean
