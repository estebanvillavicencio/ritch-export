"""Motor, sesión y base declarativa de SQLAlchemy."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

_connect_args = {}
if settings.db_url.startswith("sqlite"):
    # SQLite no entrega filas mutables a la vez que otra sesión escribe.
    _connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.db_url,
    echo=settings.sql_echo,
    future=True,
    connect_args=_connect_args,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """Base declarativa común a todos los modelos."""


def get_db() -> Generator[Session, None, None]:
    """Dependencia de FastAPI: una sesión por petición."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Crea el esquema si no existe. Importa los modelos para registrarlos."""
    from app import models  # noqa: F401  (efecto secundario: registro de metadatos)

    Base.metadata.create_all(bind=engine)
