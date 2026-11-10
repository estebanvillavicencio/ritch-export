"""Configuración de pytest.

Cada prueba corre contra una base SQLite temporal con el esquema completo y
datos mínimos, de modo que no depende de un servidor PostgreSQL.
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator

import pytest

# Base temporal antes de importar la aplicación.
_TMP = tempfile.mkdtemp(prefix="ritch-tests-")
os.environ["RITECH_DB_URL"] = f"sqlite:///{os.path.join(_TMP, 'test.db')}"
# 32 bytes: PyJWT recomienda >= 32 para HMAC-SHA256.
os.environ["RITECH_JWT_SECRET"] = "clave-de-pruebas-32-bytes-minimos-ok"
os.environ["RITECH_UPLOAD_DIR"] = os.path.join(_TMP, "uploads")
os.environ["RITECH_BACKUP_DIR"] = os.path.join(_TMP, "respaldos")

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402

CONTRASENA = "RiTech2026*"


@pytest.fixture(scope="session", autouse=True)
def esquema() -> Iterator[None]:
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db(esquema: None) -> Iterator[Session]:
    sesion = SessionLocal()
    try:
        yield sesion
    finally:
        sesion.close()


@pytest.fixture
def cliente() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def token(cliente: TestClient) -> str:
    """Token del administrador creado por el fixture `datos`."""
    r = cliente.post(
        "/api/auth/login",
        json={"correo": "admin@ritch.com", "contrasena": CONTRASENA},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture
def cab(token: str) -> dict:
    """Cabecera `Authorization` del administrador."""
    return {"Authorization": f"Bearer {token}"}


def _vaciar(db: Session) -> None:
    """Borra el contenido de todas las tablas en orden inverso al de las FK."""
    from app.database import Base

    for tabla in reversed(Base.metadata.sorted_tables):
        db.execute(tabla.delete())
    db.commit()

@pytest.fixture
def datos(db: Session, cliente: TestClient) -> dict:
    """Datos mínimos, la sesión de la base y la de HTTP (`datos['_cab']`).

    Limpia las tablas antes de sembrar: el esquema es de ámbito de sesión
    y cada prueba debe partir de un estado conocido.
    """
    from tests.datos import sembrar_minimo

    _vaciar(db)
    ctx = sembrar_minimo(db)
    ctx["_db"] = db
    r = cliente.post(
        "/api/auth/login",
        json={"correo": "admin@ritch.com", "contrasena": CONTRASENA},
    )
    assert r.status_code == 200, r.text
    ctx["_cab"] = {"Authorization": f"Bearer {r.json()['access_token']}"}
    return ctx
