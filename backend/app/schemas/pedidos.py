"""Solicitudes de pedido creadas desde el portal del cliente."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ORMModel


class SolicitudPedidoCreate(BaseModel):
    id_producto: int
    cantidad_kg: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    incoterm: str = Field(default="FOB", min_length=3, max_length=20)
    puerto_destino: str | None = Field(default=None, max_length=100)
    observaciones: str | None = Field(default=None, max_length=2000)

    @field_validator("incoterm")
    @classmethod
    def incoterm_valido(cls, valor: str) -> str:
        from app.schemas.comercial import INCOTERMS

        valor = valor.upper()
        if valor not in INCOTERMS:
            raise ValueError("Incoterm no válido")
        return valor


class SolicitudPedidoRead(ORMModel):
    id_solicitud: int
    id_cliente: int
    id_usuario: int
    id_producto: int
    cantidad_kg: Decimal
    incoterm: str
    puerto_destino: str | None = None
    observaciones: str | None = None
    estado: str
    created_at: datetime
    producto_nombre: str
    empresa: str
