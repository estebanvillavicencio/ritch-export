"""Esquemas del módulo de Logística: contenedores y envíos.

Cubre HU-11 (gestión aduanera) y HU-12 (transporte, contenedores y rutas).
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.models.enums import EstadoEnvio
from app.schemas.common import ORMModel

TIPOS_CONTENEDOR: tuple[str, ...] = ("20GP", "40GP", "40HC", "20RF", "40RF", "LCL")
TIPOS_TRANSPORTE: tuple[str, ...] = ("Marítimo", "Aéreo", "Terrestre")


# --------------------------------------------------------------------------- #
# contenedores
# --------------------------------------------------------------------------- #
class ContenedorBase(BaseModel):
    codigo: str = Field(min_length=4, max_length=20, pattern=r"^[A-Za-z0-9\-]+$")
    tipo: str = Field(default="20GP", max_length=10)
    capacidad_kg: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    naviera: str | None = Field(default=None, max_length=100)
    disponible: bool = True

    @model_validator(mode="after")
    def _tipo_valido(self) -> "ContenedorBase":
        if self.tipo not in TIPOS_CONTENEDOR:
            raise ValueError(
                f"Tipo no válido. Opciones: {', '.join(TIPOS_CONTENEDOR)}"
            )
        return self


class ContenedorCreate(ContenedorBase):
    pass


class ContenedorUpdate(BaseModel):
    tipo: str | None = Field(default=None, max_length=10)
    capacidad_kg: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    naviera: str | None = Field(default=None, max_length=100)
    disponible: bool | None = None


class ContenedorRead(ContenedorBase, ORMModel):
    id_contenedor: int


# --------------------------------------------------------------------------- #
# envios
# --------------------------------------------------------------------------- #
class EnvioBase(BaseModel):
    id_exportacion: int
    transportadora: str = Field(min_length=2, max_length=100)
    numero_seguimiento: str = Field(min_length=3, max_length=100)
    fecha_salida: date | None = None
    fecha_llegada: date | None = None
    estado: EstadoEnvio = EstadoEnvio.PROGRAMADO
    id_contenedor: int | None = None
    puerto_origen: str | None = Field(default=None, max_length=100)
    puerto_destino: str | None = Field(default=None, max_length=100)
    tipo_transporte: str = Field(default="Marítimo", max_length=20)
    costo_flete: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    temperatura_c: Decimal | None = Field(
        default=None, ge=-30, le=60, max_digits=5, decimal_places=2
    )

    @model_validator(mode="after")
    def _validaciones(self) -> "EnvioBase":
        if self.tipo_transporte not in TIPOS_TRANSPORTE:
            raise ValueError(
                f"Tipo de transporte no válido. Opciones: {', '.join(TIPOS_TRANSPORTE)}"
            )
        if self.fecha_salida and self.fecha_llegada:
            if self.fecha_llegada < self.fecha_salida:
                raise ValueError(
                    "La fecha de llegada no puede ser anterior a la de salida"
                )
        if self.estado == EstadoEnvio.ENTREGADO and not self.fecha_llegada:
            raise ValueError("Un envío entregado debe tener fecha de llegada")
        return self


class EnvioCreate(EnvioBase):
    pass


class EnvioUpdate(BaseModel):
    transportadora: str | None = Field(default=None, min_length=2, max_length=100)
    numero_seguimiento: str | None = Field(default=None, min_length=3, max_length=100)
    fecha_salida: date | None = None
    fecha_llegada: date | None = None
    estado: EstadoEnvio | None = None
    id_contenedor: int | None = None
    puerto_origen: str | None = Field(default=None, max_length=100)
    puerto_destino: str | None = Field(default=None, max_length=100)
    tipo_transporte: str | None = Field(default=None, max_length=20)
    costo_flete: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    temperatura_c: Decimal | None = Field(
        default=None, ge=-30, le=60, max_digits=5, decimal_places=2
    )


class EnvioRead(ORMModel):
    id_envio: int
    id_exportacion: int
    id_contenedor: int | None = None
    transportadora: str
    numero_seguimiento: str
    fecha_salida: date | None = None
    fecha_llegada: date | None = None
    estado: EstadoEnvio
    puerto_origen: str | None = None
    puerto_destino: str | None = None
    tipo_transporte: str
    costo_flete: Decimal | None = None
    temperatura_c: Decimal | None = None


class EnvioSeguimiento(EnvioRead):
    """Envío con los datos del cliente para el módulo de seguimiento (HU-13)."""

    cliente_nombre: str | None = None
    cliente_pais: str | None = None
    dias_transito: int | None = None
    dias_restantes: int | None = None
    etapa_actual: str | None = None
