"""HU-22 · copias de seguridad verificables.

El respaldo es un JSON con todas las tablas del modelo. Se eligió ese formato
—y no una copia del archivo SQLite— porque funciona igual sobre SQLite,
PostgreSQL y MySQL, que es lo que exige RR-003, y porque se puede inspeccionar
sin el motor original.

Cada copia guarda tamaño y SHA-256; la verificación vuelve a calcular el hash y
dice si el archivo cambió o desapareció.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base
from app.models import RegistroIntegracion, Respaldo, TipoRespaldo, Usuario


def _serializar(valor):
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    if isinstance(valor, Decimal):
        return str(valor)
    if isinstance(valor, (bytes, bytearray)):
        return valor.decode("utf-8", errors="replace")
    return valor


def directorio() -> Path:
    ruta = Path(settings.backup_dir)
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta


def _hash(ruta: Path) -> str:
    sha = hashlib.sha256()
    with ruta.open("rb") as archivo:
        for bloque in iter(lambda: archivo.read(1024 * 1024), b""):
            sha.update(bloque)
    return sha.hexdigest()


def crear(
    db: Session,
    usuario: Usuario | None = None,
    tipo: TipoRespaldo = TipoRespaldo.MANUAL,
) -> Respaldo:
    """Genera el archivo de respaldo y registra sus metadatos."""
    sello = datetime.now().strftime("%Y%m%d-%H%M%S")
    nombre = f"ritch-{sello}.json"
    destino = directorio() / nombre

    contenido: dict[str, list[dict]] = {}
    tablas = 0
    registros = 0
    for tabla in Base.metadata.sorted_tables:
        filas = db.execute(select(tabla)).mappings().all()
        contenido[tabla.name] = [
            {clave: _serializar(valor) for clave, valor in fila.items()} for fila in filas
        ]
        tablas += 1
        registros += len(filas)

    destino.write_text(
        json.dumps(
            {
                "empresa": "RiTech SAS",
                "generado_en": datetime.now().isoformat(),
                "motor": settings.db_url.split("://", 1)[0],
                "tablas": contenido,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    respaldo = Respaldo(
        nombre=nombre,
        ruta=str(destino.resolve()),
        tamano_bytes=destino.stat().st_size,
        checksum=_hash(destino),
        tipo=tipo,
        tablas=tablas,
        registros=registros,
        detalle=f"{registros} registros en {tablas} tablas",
        id_usuario=usuario.id_usuario if usuario else None,
    )
    db.add(respaldo)
    db.add(
        RegistroIntegracion(
            servicio="Almacenamiento documental",
            accion="Crear respaldo",
            estado="ok",
            mensaje=f"Respaldo {nombre} creado con {registros} registros.",
            detalle=json.dumps({"nombre": nombre, "tablas": tablas, "registros": registros}),
        )
    )
    db.flush()
    return respaldo


def verificar(respaldo: Respaldo) -> dict:
    ruta = Path(respaldo.ruta)
    if not ruta.is_file():
        return {
            "id_respaldo": respaldo.id_respaldo,
            "nombre": respaldo.nombre,
            "existe": False,
            "checksum_actual": None,
            "checksum_registrado": respaldo.checksum,
            "integro": False,
            "mensaje": "El archivo de respaldo ya no está en disco.",
        }
    actual = _hash(ruta)
    integro = respaldo.checksum is None or actual == respaldo.checksum
    return {
        "id_respaldo": respaldo.id_respaldo,
        "nombre": respaldo.nombre,
        "existe": True,
        "checksum_actual": actual,
        "checksum_registrado": respaldo.checksum,
        "integro": integro,
        "mensaje": (
            "El respaldo coincide con el hash registrado."
            if integro
            else "El archivo cambió desde que se creó el respaldo."
        ),
    }


def listar(db: Session, limite: int = 50) -> list[Respaldo]:
    return db.scalars(
        select(Respaldo)
        .order_by(Respaldo.created_at.desc(), Respaldo.id_respaldo.desc())
        .limit(limite)
    ).all()


def ultimo(db: Session) -> Respaldo | None:
    return db.scalar(
        select(Respaldo).order_by(Respaldo.created_at.desc(), Respaldo.id_respaldo.desc())
    )


def automatico_si_hace_falta(db: Session, horas: int | None = None) -> Respaldo | None:
    """Crea una copia automática si la última tiene más de `horas`."""
    horas = horas if horas is not None else settings.backup_auto_horas
    limite = datetime.now() - timedelta(hours=max(1, horas))
    reciente = db.scalar(
        select(Respaldo)
        .where(Respaldo.created_at >= limite, Respaldo.estado == "Completado")
        .order_by(Respaldo.created_at.desc())
    )
    if reciente is not None:
        return None
    respaldo = crear(db, tipo=TipoRespaldo.AUTOMATICO)
    db.commit()
    db.refresh(respaldo)
    return respaldo


def ruta_de(respaldo: Respaldo) -> Path:
    ruta = Path(respaldo.ruta)
    if not ruta.is_file():
        raise ValueError("El archivo del respaldo no existe en disco")
    return ruta


def contar_tablas(db: Session) -> int:
    return int(db.scalar(select(func.count()).select_from(Base.metadata.tables["usuarios"])) or 0)
