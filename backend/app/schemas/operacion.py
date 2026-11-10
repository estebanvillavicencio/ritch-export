"""Esquemas del módulo de Productores, Lotes y Trazabilidad, y del módulo de Calidad.

Cubre HU-04 (registrar fincas), HU-05 (inventario de lotes), HU-06 (trazabilidad)
y HU-17 (catación y laboratorio).
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.models.enums import (
    EstadoCalidad,
    EstadoCertificacion,
    EtapaTrazabilidad,
    TipoCertificacion,
)
from app.schemas.catalogos import CertificacionResumida
from app.schemas.common import ORMModel

#: Humedad máxima aceptada para café y cacao verdes (%).
HUMEDAD_MAXIMA = 14.0
#: Humedad mínima aceptada.
HUMEDAD_MINIMA = 8.0


# --------------------------------------------------------------------------- #
# lotes · HU-05
# --------------------------------------------------------------------------- #
class LoteBase(BaseModel):
    id_finca: int
    id_producto: int
    cantidad_kg: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    fecha_cosecha: date
    variedad: str | None = Field(default=None, max_length=100)
    altura_msnm: int | None = Field(default=None, ge=0, le=4000)
    estado_calidad: EstadoCalidad = EstadoCalidad.PENDIENTE

    @model_validator(mode="after")
    def _sin_cosecha_futura(self) -> "LoteBase":
        if self.fecha_cosecha > date.today():
            raise ValueError("La fecha de cosecha no puede ser futura")
        return self


class LoteCreate(LoteBase):
    codigo_lote: str | None = Field(default=None, max_length=50)


class LoteUpdate(BaseModel):
    id_finca: int | None = None
    id_producto: int | None = None
    cantidad_kg: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    fecha_cosecha: date | None = None
    variedad: str | None = Field(default=None, max_length=100)
    altura_msnm: int | None = Field(default=None, ge=0, le=4000)
    estado_calidad: EstadoCalidad | None = None


class LoteRead(ORMModel):
    id_lote: int
    codigo_lote: str
    id_finca: int
    id_producto: int
    cantidad_kg: Decimal
    disponible_kg: Decimal | None = None
    consumo_kg: Decimal
    fecha_cosecha: date
    estado_calidad: EstadoCalidad
    variedad: str | None = None
    altura_msnm: int | None = None
    created_at: datetime | None = None


class LoteDetallado(LoteRead):
    """Lote con sus relaciones cargadas, para la ficha de lote del panel."""

    finca_nombre: str | None = None
    finca_ubicacion: str | None = None
    finca_departamento: str | None = None
    finca_propietario: str | None = None
    finca_asociacion: str | None = None
    producto_nombre: str | None = None
    producto_tipo: str | None = None
    certificaciones: list[CertificacionResumida] = Field(default_factory=list)
    calidad: "CalidadRead | None" = None


# --------------------------------------------------------------------------- #
# calidad_lote · HU-17
# --------------------------------------------------------------------------- #
class CalidadBase(BaseModel):
    humedad: Decimal | None = Field(
        default=None, ge=0, le=100, max_digits=5, decimal_places=2
    )
    puntaje_cata: Decimal | None = Field(
        default=None, ge=0, le=100, max_digits=6, decimal_places=2
    )
    actividad_agua: Decimal | None = Field(default=None, ge=0, max_digits=5, decimal_places=2)
    granulometria: Decimal | None = Field(default=None, ge=0, max_digits=5, decimal_places=2)
    impurezas: Decimal | None = Field(default=None, ge=0, max_digits=5, decimal_places=2)
    cafeina_pct: Decimal | None = Field(default=None, ge=0, max_digits=5, decimal_places=2)
    grasa_pct: Decimal | None = Field(default=None, ge=0, max_digits=5, decimal_places=2)
    prueba_metodos: str | None = Field(default=None, max_length=200)
    clasificacion: str | None = Field(default=None, max_length=50)
    laboratorio: str | None = Field(default=None, max_length=150)
    observaciones: str | None = None
    fecha_analisis: date | None = None
    aprobado_por: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def _humedad_en_rango(self) -> "CalidadBase":
        if self.humedad is not None and not (
            HUMEDAD_MINIMA <= float(self.humedad) <= HUMEDAD_MAXIMA
        ):
            raise ValueError(
                f"La humedad debe estar entre {HUMEDAD_MINIMA}% y {HUMEDAD_MAXIMA}%"
            )
        return self


class CalidadCreate(CalidadBase):
    id_lote: int


class CalidadUpdate(BaseModel):
    humedad: Decimal | None = Field(default=None, ge=0, le=100, max_digits=5, decimal_places=2)
    puntaje_cata: Decimal | None = Field(default=None, ge=0, le=100, max_digits=6, decimal_places=2)
    actividad_agua: Decimal | None = Field(default=None, ge=0, max_digits=5, decimal_places=2)
    granulometria: Decimal | None = Field(default=None, ge=0, max_digits=5, decimal_places=2)
    impurezas: Decimal | None = Field(default=None, ge=0, max_digits=5, decimal_places=2)
    cafeina_pct: Decimal | None = Field(default=None, ge=0, max_digits=5, decimal_places=2)
    grasa_pct: Decimal | None = Field(default=None, ge=0, max_digits=5, decimal_places=2)
    prueba_metodos: str | None = Field(default=None, max_length=200)
    clasificacion: str | None = Field(default=None, max_length=50)
    laboratorio: str | None = Field(default=None, max_length=150)
    observaciones: str | None = None
    fecha_analisis: date | None = None
    aprobado_por: str | None = Field(default=None, max_length=100)


class CalidadRead(CalidadBase, ORMModel):
    id_calidad: int
    id_lote: int


# --------------------------------------------------------------------------- #
# certificaciones · Informe §6.4
# --------------------------------------------------------------------------- #
class CertificacionBase(BaseModel):
    tipo: TipoCertificacion
    entidad_emisora: str | None = Field(default=None, max_length=150)
    numero_certificado: str | None = Field(default=None, max_length=100)
    fecha_emision: date
    fecha_vencimiento: date | None = None
    lote_georreferenciado: bool = False
    notas: str | None = None

    @model_validator(mode="after")
    def _vencimiento_posterior(self) -> "CertificacionBase":
        if (
            self.fecha_vencimiento
            and self.fecha_vencimiento < self.fecha_emision
        ):
            raise ValueError(
                "La fecha de vencimiento no puede ser anterior a la de emisión"
            )
        return self


class CertificacionCreate(CertificacionBase):
    id_lote: int | None = None
    id_finca: int | None = None

    @model_validator(mode="after")
    def _requiere_propietario(self) -> "CertificacionCreate":
        if self.id_lote is None and self.id_finca is None:
            raise ValueError("La certificación debe pertenecer a un lote o a una finca")
        return self


class CertificacionRead(CertificacionBase, ORMModel):
    id_certificacion: int
    id_lote: int | None = None
    id_finca: int | None = None
    archivo: str | None = None
    #: Derivado de las fechas de emisión y vencimiento; no se almacena.
    estado: str = EstadoCertificacion.PENDIENTE.value
    dias_para_vencer: int | None = None


# --------------------------------------------------------------------------- #
# eventos_trazabilidad · HU-06
# --------------------------------------------------------------------------- #
class EventoBase(BaseModel):
    etapa: EtapaTrazabilidad
    fecha: date
    ubicacion: str | None = Field(default=None, max_length=150)
    descripcion: str | None = Field(default=None, max_length=300)
    id_envio: int | None = None


class EventoCreate(EventoBase):
    id_lote: int


class EventoRead(EventoBase, ORMModel):
    id_evento: int
    id_lote: int
    documento: str | None = None


class EtapaTrazabilidadEstado(BaseModel):
    """Una etapa de la línea de tiempo con su estado, para el panel general."""

    etapa: EtapaTrazabilidad
    fecha: date | None = None
    ubicacion: str | None = None
    descripcion: str | None = None
    estado: str = Field(description="done | current | pending")


class TrazabilidadRead(BaseModel):
    id_lote: int
    codigo_lote: str
    etapas: list[EtapaTrazabilidadEstado]


LoteDetallado.model_rebuild()
