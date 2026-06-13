"""Camada de ligação MongoDB.

O projeto usa PyMongo em execução normal. Para testes e demonstrações sem
MongoDB instalado, existe uma pequena base em memória com os métodos usados
pela aplicação. A arquitetura continua igual: rotas -> serviços -> coleções.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


try:
    from bson import ObjectId
    from pymongo import MongoClient
except Exception:  # pragma: no cover - só acontece quando dependências faltam.
    ObjectId = None
    MongoClient = None


class InsertResult:
    """Resultado mínimo compatível com PyMongo insert_one."""

    def __init__(self, inserted_id: str):
        self.inserted_id = inserted_id


class InsertManyResult:
    """Resultado mínimo compatível com PyMongo insert_many."""

    def __init__(self, inserted_ids: list[str]):
        self.inserted_ids = inserted_ids


class UpdateResult:
    """Resultado mínimo compatível com PyMongo update_one."""

    def __init__(self, modified_count: int):
        self.modified_count = modified_count


class DeleteResult:
    """Resultado mínimo compatível com PyMongo delete_one."""

    def __init__(self, deleted_count: int):
        self.deleted_count = deleted_count


class MemoryCollection:
    """Coleção em memória com uma fração da API do PyMongo."""

    def __init__(self):
        self.rows: list[dict[str, Any]] = []

    def _matches(self, document: dict[str, Any], query: dict[str, Any] | None) -> bool:
        """Verifica se um documento satisfaz igualdade simples e operadores comuns."""

        if not query:
            return True
        for key, expected in query.items():
            value = document.get(key)
            if isinstance(expected, dict):
                if "$ne" in expected and value == expected["$ne"]:
                    return False
                if "$in" in expected and value not in expected["$in"]:
                    return False
            elif value != expected:
                return False
        return True

    def insert_one(self, document: dict[str, Any]) -> InsertResult:
        """Insere um documento e cria _id se ainda não existir."""

        saved = deepcopy(document)
        saved.setdefault("_id", str(uuid4()))
        self.rows.append(saved)
        return InsertResult(str(saved["_id"]))

    def insert_many(self, documents: list[dict[str, Any]]) -> InsertManyResult:
        """Insere vários documentos de uma vez."""

        ids = [self.insert_one(document).inserted_id for document in documents]
        return InsertManyResult(ids)

    def find_one(self, query: dict[str, Any] | None = None) -> dict[str, Any] | None:
        """Retorna o primeiro documento que corresponde ao filtro."""

        for document in self.rows:
            if self._matches(document, query):
                return deepcopy(document)
        return None

    def find(self, query: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Retorna todos os documentos que correspondem ao filtro."""

        return [deepcopy(document) for document in self.rows if self._matches(document, query)]

    def count_documents(self, query: dict[str, Any] | None = None) -> int:
        """Conta documentos filtrados."""

        return len(self.find(query))

    def update_one(self, query: dict[str, Any], update: dict[str, Any]) -> UpdateResult:
        """Atualiza o primeiro documento encontrado."""

        for document in self.rows:
            if self._matches(document, query):
                if "$set" in update:
                    document.update(update["$set"])
                return UpdateResult(1)
        return UpdateResult(0)

    def delete_one(self, query: dict[str, Any]) -> DeleteResult:
        """Remove o primeiro documento encontrado."""

        for index, document in enumerate(self.rows):
            if self._matches(document, query):
                del self.rows[index]
                return DeleteResult(1)
        return DeleteResult(0)

    def delete_many(self, query: dict[str, Any] | None = None) -> DeleteResult:
        """Remove vários documentos; útil em testes."""

        before = len(self.rows)
        self.rows = [row for row in self.rows if not self._matches(row, query)]
        return DeleteResult(before - len(self.rows))


class MemoryDatabase(dict):
    """Contentor de coleções em memória."""

    def __getitem__(self, name: str) -> MemoryCollection:
        if name not in self:
            self[name] = MemoryCollection()
        return dict.__getitem__(self, name)


mongo_client = None
db = MemoryDatabase()


def init_db(app):
    """Inicializa MongoDB real ou base em memória conforme a configuração."""

    global mongo_client, db
    if app.config.get("USE_MEMORY_DB") or MongoClient is None:
        db = MemoryDatabase()
    else:
        try:
            mongo_client = MongoClient(app.config["MONGO_URI"], serverSelectionTimeoutMS=800)
            mongo_client.admin.command("ping")
            db = mongo_client[app.config["MONGO_DB_NAME"]]
        except Exception:
            # Mantém a aplicação executável para apresentação mesmo sem MongoDB local.
            db = MemoryDatabase()

    ensure_indexes()
    return db


def get_db():
    """Disponibiliza a base de dados para modelos e serviços."""

    return db


def ensure_indexes():
    """Cria índices quando a base real MongoDB está disponível."""

    try:
        db["users"].create_index("email", unique=True)
        db["api_keys"].create_index("key", unique=True)
        db["survey_responses"].create_index("province")
        db["jwt_blocklist"].create_index("jti", unique=True)
    except Exception:
        # A base em memória não precisa de índices.
        return


def normalize_id(value: Any) -> Any:
    """Converte strings para ObjectId quando possível."""

    if ObjectId is None:
        return value
    try:
        return ObjectId(value)
    except Exception:
        return value


def now_utc() -> datetime:
    """Fornece timestamps consistentes para documentos."""

    return datetime.now(UTC)
