"""Esquemas del módulo Comercial: cotizaciones, exportaciones y documentos.

Cubre HU-03 (clientes UE), HU-08 (cotizaciones y contratos), HU-09 (pedidos),
HU-10 (documentación) y HU-11 (gestión aduanera).
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.models.enums import (
    EstadoCotizacion,
    EstadoDocumento,
    EstadoExportacion,
    TipoDocumento,
)
from app.schemas.catalogos import ClienteResumen
from app.schemas.common import ORMModel
from app.schemas.logistica import EnvioRead

#: Incoterms vigentes (Incoterms® 2020).
INCOTERMS: tuple[str, ...] = (
    "EXW",
    "FCA",
    "CPT",
    "CIP",
    "DAP",
    "DPU",
    "DDP",
    "FAS",
    "FOB",
    "CFR",
    "CIF",
)


# --------------------------------------------------------------------------- #
# cotizaciones · HU-08
# --------------------------------------------------------------------------- #
class CotizacionBase(BaseModel):
    id_cliente: int
    cantidad_kg: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    precio_kg: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    moneda: str = Field(default="EUR", max_length=10)
    incoterm: str = Field(default="FOB", max_length=20)
    fecha: date
    validez_dias: int = Field(default=15, ge=1, le=365)
    puerto_origen: str | None = Field(default=None, max_length=100)
    puerto_destino: str | None = Field(default=None, max_length=100)
    observaciones: str | None = None

    @model_validator(mode="after")
    def _incoterm_valido(self) -> "CotizacionBase":
        if self.incoterm not in INCOTERMS:
            raise ValueError(
                f"Incoterm no válido. Opciones: {', '.join(INCOTERMS)}"
            )
        return self


class CotizacionCreate(CotizacionBase):
    numero: str | None = Field(default=None, max_length=60)


class CotizacionUpdate(BaseModel):
    cantidad_kg: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    precio_kg: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    moneda: str | None = Field(default=None, max_length=10)
    incoterm: str | None = Field(default=None, max_length=20)
    fecha: date | None = None
    validez_dias: int | None = Field(default=None, ge=1, le=365)
    puerto_origen: str | None = Field(default=None, max_length=100)
    puerto_destino: str | None = Field(default=None, max_length=100)
    observaciones: str | None = None
    estado: EstadoCotizacion | None = None


class CotizacionRead(CotizacionBase, ORMModel):
    id_cotizacion: int
    numero: str
    id_usuario: int
    estado: EstadoCotizacion
    valor_total: float
    created_at: datetime | None = None
    cliente: ClienteResumen | None = None


class CotizacionConversion(BaseModel):
    """Cuerpo de la conversión de una cotización en exportación."""

    lotes: list[str] = Field(
        min_length=1, description="Códigos de lote a asignar a la exportación"
    )
    cantidad_por_lote: dict[str, Decimal] = Field(
        default_factory=dict,
        description="Cantidad en kg por código de lote; si falta, se usa cantidad_default",
    )
    cantidad_default: Decimal = Field(
        default=Decimal("0"), ge=0, max_digits=12, decimal_places=2
    )

    @model_validator(mode="after")
    def _validar(self) -> "CotizacionConversion":
        if not self.cantidad_default and not self.cantidad_por_lote:
            raise ValueError(
                "Indica cantidad_default o una cantidad por lote para asignar los kilos"
            )
        for codigo in self.cantidad_por_lote:
            if codigo not in self.lotes:
                raise ValueError(
                    f"La cantidad de {codigo} no corresponde a ningún lote indicado"
                )
        return self


# --------------------------------------------------------------------------- #
# detalle_exportacion
# --------------------------------------------------------------------------- #
class DetalleBase(BaseModel):
    id_lote: int
    cantidad_kg: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    precio_kg: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class DetalleCreate(DetalleBase):
    pass


class DetalleRead(DetalleBase, ORMModel):
    id_detalle: int
    id_exportacion: int
    subtotal: float


# --------------------------------------------------------------------------- #
# exportaciones
# --------------------------------------------------------------------------- #
class ExportacionCreate(BaseModel):
    id_cliente: int
    fecha: date
    id_usuario: int | None = Field(
        default=None, description="Si se omite, se toma el usuario autenticado"
    )
    moneda: str = Field(default="EUR", max_length=10)
    incoterm: str | None = Field(default=None, max_length=20)
    puerto_origen: str | None = Field(default=None, max_length=100)
    puerto_destino: str | None = Field(default=None, max_length=100)
    observaciones: str | None = None
    detalles: list[DetalleCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def _sin_lotes_repetidos(self) -> "ExportacionCreate":
        ids = [d.id_lote for d in self.detalles]
        if len(ids) != len(set(ids)):
            raise ValueError("Un lote no puede repetirse dentro de la misma exportación")
        return self


class ExportacionUpdate(BaseModel):
    estado: EstadoExportacion | None = None
    fecha: date | None = None
    incoterm: str | None = Field(default=None, max_length=20)
    puerto_origen: str | None = Field(default=None, max_length=100)
    puerto_destino: str | None = Field(default=None, max_length=100)
    observaciones: str | None = None
    detalles: list[DetalleCreate] | None = None


class ExportacionRead(ORMModel):
    id_exportacion: int
    id_cliente: int
    id_usuario: int
    numero_contrato: str | None = None
    fecha: date
    estado: EstadoExportacion
    moneda: str
    incoterm: str | None = None
    puerto_origen: str | None = None
    puerto_destino: str | None = None
    valor_total: Decimal
    observaciones: str | None = None
    total_kg: float
    dias_transito: int | None = None
    created_at: datetime | None = None
    cliente: ClienteResumen | None = None
    detalles: list[DetalleRead] = Field(default_factory=list)
    documentos: list["DocumentoRead"] = Field(default_factory=list)
    envios: list[EnvioRead] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# documentos_exportacion · HU-10
# --------------------------------------------------------------------------- #
class DocumentoBase(BaseModel):
    tipo_documento: TipoDocumento
    numero_documento: str = Field(min_length=2, max_length=100)
    fecha_emision: date
    estado: EstadoDocumento = EstadoDocumento.BORRADOR
    autorizado_cliente: bool = False


class DocumentoCreate(DocumentoBase):
    id_exportacion: int


class DocumentoUpdate(BaseModel):
    tipo_documento: TipoDocumento | None = None
    numero_documento: str | None = Field(default=None, min_length=2, max_length=100)
    fecha_emision: date | None = None
    estado: EstadoDocumento | None = None
    autorizado_cliente: bool | None = None


class DocumentoRead(DocumentoBase, ORMModel):
    id_documento: int
    id_exportacion: int
    archivo: str | None = None
    tamano_bytes: int | None = None


class DocumentoGenerado(BaseModel):
    """Documento renderizado en formato imprimible."""

    id_documento: int
    tipo_documento: TipoDocumento
    numero_documento: str
    fecha_emision: date
    contenido: dict


ExportacionRead.model_rebuild()
