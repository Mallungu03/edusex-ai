"""Gera um dataset sintético de 1500 respostas e insere em `survey_responses`.

Distribuição: Uíge com maior número de registos conforme pedido.
Este script pode ser executado localmente: `python scripts/generate_dataset.py`.
"""
from __future__ import annotations

import random
from datetime import datetime

from database.mongodb import init_db, get_db
from models.survey import create_survey_document


PROVINCES = [
    "Luanda",
    "Bengo",
    "Benguela",
    "Bié",
    "Cabinda",
    "Cuando Cubango",
    "Cuanza Norte",
    "Cuanza Sul",
    "Cunene",
    "Huambo",
    "Huíla",
    "Lunda Norte",
    "Lunda Sul",
    "Malanje",
    "Moxico",
    "Namibe",
    "Uíge",
    "Zaire",
]


def random_response(province: str) -> dict:
    age = random.randint(13, 24)
    gender = random.choice(["M", "F"])
    received = random.random() < 0.6
    who = random.choice(["Pais", "Irmãos/as", "Colegas", "Médico/a", "Professor/a", "Outro"])
    source = random.choice(["Pais", "Irmãos/as", "Colegas", "Médico", "Internet", "Professor/a", "Outro"])
    school = random.random() < 0.5
    parents_main = random.random() < 0.4
    support = random.random() < 0.5
    support_loc = random.choice(["Na escola como disciplina específica", "Na escola, num gabinete de apoio", "Outro"]) if support else ""
    had_sex = random.random() < 0.45
    had_std = had_sex and (random.random() < 0.07)
    std_details = "Gonorreia" if had_std and random.random() < 0.5 else ("Clamídia" if had_std else "")
    contraceptive = had_sex and (random.random() < 0.6)
    methods = []
    if contraceptive:
        choices = ["Pílula", "Preservativo", "Pílula do dia seguinte", "Outro"]
        methods = random.sample(choices, k=random.randint(1, min(2, len(choices))))
    need_info = random.random() < 0.65
    pressured = random.random() < 0.1
    friends_discuss = random.random() < 0.5
    embarrassed = random.random() < 0.5

    payload = {
        "age": age,
        "gender": gender,
        "province": province,
        "municipality": f"Município-{random.randint(1,50)}",
        "receivedSexEducation": received,
        "who_talked": who,
        "sourceOfInformation": source,
        "schoolEducation": school,
        "parents_main_educators": parents_main,
        "support_structure": support,
        "support_structure_location": support_loc,
        "had_sexual_relations": had_sex,
        "had_std": had_std,
        "std_details": std_details,
        "contraceptiveUse": contraceptive,
        "contraceptive_methods": methods,
        "needMoreInformation": need_info,
        "pressuredToHaveSex": pressured,
        "friends_discuss": friends_discuss,
        "feelsEmbarrassed": embarrassed,
    }
    return payload


def generate(total=1500):
    # Distribution: Uíge gets 400, others share remaining
    counts = {}
    remaining = total - 400
    others = [p for p in PROVINCES if p != "Uíge"]
    base = remaining // len(others)
    for p in others:
        counts[p] = base
    # distribute remainder
    rem = remaining - base * len(others)
    for i in range(rem):
        counts[others[i % len(others)]] += 1
    counts["Uíge"] = 400

    records = []
    for p, c in counts.items():
        for _ in range(c):
            records.append(create_survey_document(random_response(p)))

    return records


if __name__ == "__main__":
    # Inicializa DB com configuração padrão (espera app env ou MEMORY)
    from pathlib import Path
    from dotenv import load_dotenv

    load_dotenv()
    # Tentativa simples de inicializar DB em modo standalone
    # Requer que a aplicação esteja configurada para usar USE_MEMORY_DB em tests
    try:
        # Criamos uma app temporária para inicializar a DB quando necessário
        from flask import Flask
        app = Flask(__name__)
        app.config["USE_MEMORY_DB"] = True
        init_db(app)
    except Exception:
        pass

    db = get_db()
    records = generate(1500)
    # Limpa e insere
    try:
        db["survey_responses"].delete_many({})
    except Exception:
        pass
    db["survey_responses"].insert_many(records)
    print(f"Inserted {len(records)} synthetic survey_responses at {datetime.utcnow().isoformat()}.")
