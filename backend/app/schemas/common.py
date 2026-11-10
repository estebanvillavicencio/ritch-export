"""Utilidades comunes a todos los esquemas."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ORMModel(BaseModel):
    """Base para leer desde modelos SQLAlchemy."""

    model_config = ConfigDict(from_attributes=True)


class Mensaje(BaseModel):
    """Respuesta simple de confirmación."""

    mensaje: str
    id: int | None = None


class Paginado(BaseModel, Generic[T]):
    """Envoltorio de listas paginadas."""

    items: list[T]
    total: int
    pagina: int = 1
    tamano: int = 20


class FiltroFecha(BaseModel):
    desde: date | None = None
    hasta: date | None = None


#: Redondeo a dos decimales para importes y pesos.
def d2(value: Decimal | None) -> float | None:
    return None if value is None else float(round(value, 2))


class ResumenTarjeta(BaseModel):
    """Datos para las tarjetas KPI del panel general."""

    etiqueta: str
    valor: str
    detalle: str | None = None
    tono: str = Field(default="neutro", description="leaf | eu-blue | gold | rust")
    tendencia: str | None = None
    tendencia_sube: bool | None = None
