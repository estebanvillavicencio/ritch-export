"""HU-19 · multimoneda y HU-20 · integración de tipos de cambio.

La tasa se guarda como **unidades de la moneda por 1 EUR**:

    1 EUR = 1,09 USD  →  moneda='USD', tasa=1.09
    1 EUR = 4.300 COP →  moneda='COP', tasa=4300

El servicio intenta consultar un proveedor público cuando
``RITECH_INTEGRACIONES_RED=1``; si no hay red o el servicio falla, usa un
respaldo local determinista. En ambos casos deja el intento en
``registros_integracion`` y guarda las tasas del día en ``tipos_cambio``.
"""

from __future__ import annotations

import json
import urllib.request
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import RegistroIntegracion, TipoCambio

#: Respaldo local. El valor es cuántas unidades de la moneda equivalen a 1 EUR.
TASAS_RESPALDO: dict[str, Decimal] = {
    "EUR": Decimal("1"),
    "USD": Decimal("1.09"),
    "COP": Decimal("4300"),
}

FUENTE_RED = "https://api.frankfurter.app/latest?from=EUR&to=USD"
FUENTE_LOCAL = "Respaldo local RiTech"


class ErrorMoneda(ValueError):
    """Moneda no soportada o tasa no disponible."""


def normalizar(moneda: str) -> str:
    return (moneda or "EUR").strip().upper()


def tasa(db: Session, moneda: str, fecha: date | None = None) -> Decimal:
    """Tasa vigente de una moneda contra el euro."""
    moneda = normalizar(moneda)
    if moneda == "EUR":
        return Decimal("1")
    consulta = select(TipoCambio).where(TipoCambio.moneda == moneda)
    if fecha is not None:
        consulta = consulta.where(TipoCambio.fecha <= fecha)
    fila = db.scalar(consulta.order_by(TipoCambio.fecha.desc(), TipoCambio.id_tipo_cambio.desc()))
    if fila is not None:
        return Decimal(str(fila.tasa))
    if moneda in TASAS_RESPALDO:
        return TASAS_RESPALDO[moneda]
    raise ErrorMoneda(f"No hay tipo de cambio para la moneda {moneda}")


def convertir(
    db: Session, valor: Decimal | float, desde: str, hasta: str, fecha: date | None = None
) -> Decimal:
    """Convierte un importe entre dos monedas usando las tasas vigentes."""
    origen = tasa(db, desde, fecha)
    destino = tasa(db, hasta, fecha)
    return Decimal(str(valor)) / origen * destino


def a_eur(db: Session, valor: Decimal | float, moneda: str, fecha: date | None = None) -> Decimal:
    return convertir(db, valor, moneda, "EUR", fecha)


def listar(db: Session) -> list[TipoCambio]:
    """Última tasa conocida de cada moneda, en orden alfabético."""
    ultimas: list[TipoCambio] = []
    for moneda in sorted({*TASAS_RESPALDO, *[m for (m,) in db.execute(select(TipoCambio.moneda)).all()]}):
        if moneda == "EUR":
            continue
        fila = db.scalar(
            select(TipoCambio)
            .where(TipoCambio.moneda == moneda)
            .order_by(TipoCambio.fecha.desc(), TipoCambio.id_tipo_cambio.desc())
        )
        if fila is not None:
            ultimas.append(fila)
    return ultimas


def _consultar_red() -> tuple[dict[str, Decimal], str] | None:
    """Consulta el proveedor público. Devuelve ``None`` si no hay red."""
    if not settings.integraciones_red:
        return None
    try:
        with urllib.request.urlopen(FUENTE_RED, timeout=settings.integraciones_timeout) as r:
            datos = json.loads(r.read().decode("utf-8"))
        tasas = {m: Decimal(str(v)) for m, v in datos.get("rates", {}).items()}
        if tasas:
            return tasas, "Frankfurter (BCE)"
    except Exception:  # noqa: BLE001 — cualquier fallo de red cae al respaldo
        return None
    return None


def actualizar(db: Session, hoy: date | None = None) -> dict:
    """Actualiza las tasas del día. Es idempotente por (moneda, fecha)."""
    hoy = hoy or date.today()
    consulta = _consultar_red()
    if consulta is None:
        tasas, fuente, modo = dict(TASAS_RESPALDO), FUENTE_LOCAL, "respaldo local"
        estado = "simulado"
        mensaje = "Sin conexión al proveedor; se usaron las tasas de respaldo."
    else:
        tasas, fuente = consulta
        tasas["EUR"] = Decimal("1")
        modo = "servicio"
        estado = "ok"
        mensaje = f"Tasas obtenidas de {fuente}."

    actualizados = 0
    for moneda, valor in tasas.items():
        if moneda == "EUR":
            continue
        fila = db.scalar(
            select(TipoCambio).where(
                TipoCambio.moneda == moneda, TipoCambio.fecha == hoy
            )
        )
        if fila is None:
            db.add(
                TipoCambio(
                    moneda=moneda,
                    tasa=Decimal(str(valor)),
                    fecha=hoy,
                    fuente=fuente,
                )
            )
        else:
            fila.tasa = Decimal(str(valor))
            fila.fuente = fuente
        actualizados += 1

    db.add(
        RegistroIntegracion(
            servicio="Tipos de cambio",
            accion="Actualizar tasas",
            estado=estado,
            mensaje=mensaje,
            detalle=json.dumps({"modo": modo, "monedas": list(tasas), "fecha": hoy.isoformat()}),
        )
    )
    db.flush()
    return {
        "actualizados": actualizados,
        "fuente": fuente,
        "fecha": hoy,
        "tasas": {m: float(v) for m, v in tasas.items()},
        "modo": modo,
    }
