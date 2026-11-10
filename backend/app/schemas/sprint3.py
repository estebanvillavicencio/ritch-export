"""Esquemas de los módulos del Sprint 3 y del Sprint 4.

Sprint 3: pagos (HU-14), notificaciones (HU-16) y auditoría (HU-21).
Sprint 4: tipos de cambio (HU-19), integraciones (HU-20) y respaldos (HU-22).
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.models.enums import (
    EstadoPago,
    EstadoRespaldo,
    MetodoPago,
    TipoNotificacion,
    TipoPago,
    TipoRespaldo,
)
from app.schemas.common import ORMModel


# --------------------------------------------------------------------------- #
# pagos · HU-14
# --------------------------------------------------------------------------- #
class PagoBase(BaseModel):
    id_exportacion: int
    fecha: date
    tipo: TipoPago = TipoPago.ANTICIPO
    metodo: MetodoPago = MetodoPago.TRANSFERENCIA
    estado: EstadoPago = EstadoPago.REGISTRADO
    valor: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    moneda: str = Field(default="EUR", max_length=10)
    referencia: str | None = Field(default=None, max_length=100)
    banco: str | None = Field(default=None, max_length=150)
    observaciones: str | None = None


class PagoCreate(PagoBase):
    pass


class PagoUpdate(BaseModel):
    fecha: date | None = None
    tipo: TipoPago | None = None
    metodo: MetodoPago | None = None
    estado: EstadoPago | None = None
    valor: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    moneda: str | None = Field(default=None, max_length=10)
    referencia: str | None = Field(default=None, max_length=100)
    banco: str | None = Field(default=None, max_length=150)
    observaciones: str | None = None


class PagoRead(PagoBase, ORMModel):
    id_pago: int
    id_usuario: int
    created_at: datetime | None = None
    numero_contrato: str | None = None
    cliente: str | None = None


class PagoResumenMoneda(BaseModel):
    moneda: str
    contratado: float
    cobrado: float
    pendiente: float
    anticipos: float


class PagoResumenExportacion(BaseModel):
    id_exportacion: int
    numero_contrato: str | None = None
    cliente: str
    moneda: str
    estado: str
    valor_total: float
    cobrado: float
    pendiente: float
    porcentaje: float


class FinancieroResumen(BaseModel):
    """Indicadores del módulo financiero."""

    total_contratado: float
    total_cobrado: float
    total_pendiente: float
    total_anticipos: float
    pagos_confirmados: int
    pagos_registrados: int
    pagos_anulados: int
    contratos_con_saldo: int
    cartera_vencida: float
    por_moneda: list[PagoResumenMoneda] = Field(default_factory=list)
    por_exportacion: list[PagoResumenExportacion] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# notificaciones · HU-16
# --------------------------------------------------------------------------- #
class NotificacionBase(BaseModel):
    tipo: TipoNotificacion = TipoNotificacion.SISTEMA
    tono: str = Field(default="azul", max_length=20)
    titulo: str = Field(min_length=3, max_length=200)
    detalle: str | None = None
    enlace: str | None = Field(default=None, max_length=200)
    rol_destino: str | None = Field(default=None, max_length=50)
    id_usuario: int | None = None


class NotificacionCreate(NotificacionBase):
    clave: str | None = Field(default=None, max_length=160)


class NotificacionRead(NotificacionBase, ORMModel):
    id_notificacion: int
    clave: str | None = None
    leida: bool
    fecha: datetime


class ContadorNotificaciones(BaseModel):
    total: int
    no_leidas: int


# --------------------------------------------------------------------------- #
# auditoría · HU-21
# --------------------------------------------------------------------------- #
class AuditoriaRead(ORMModel):
    id_auditoria: int
    id_usuario: int | None = None
    usuario_correo: str | None = None
    accion: str
    entidad: str | None = None
    id_entidad: str | None = None
    detalle: str | None = None
    metodo: str | None = None
    ruta: str | None = None
    estado_http: int | None = None
    ip: str | None = None
    fecha: datetime


# --------------------------------------------------------------------------- #
# multimoneda · HU-19
# --------------------------------------------------------------------------- #
class TipoCambioBase(BaseModel):
    moneda: str = Field(min_length=3, max_length=10)
    tasa: Decimal = Field(gt=0, max_digits=18, decimal_places=6)
    fecha: date
    fuente: str | None = Field(default=None, max_length=100)


class TipoCambioCreate(TipoCambioBase):
    pass


class TipoCambioRead(TipoCambioBase, ORMModel):
    id_tipo_cambio: int
    created_at: datetime | None = None


class ConversionMoneda(BaseModel):
    valor: float
    desde: str = "EUR"
    hasta: str = "EUR"
    resultado: float
    tasa: float
    fecha: date


# --------------------------------------------------------------------------- #
# respaldos · HU-22
# --------------------------------------------------------------------------- #
class RespaldoRead(ORMModel):
    id_respaldo: int
    nombre: str
    ruta: str
    tamano_bytes: int
    checksum: str | None = None
    tipo: TipoRespaldo
    estado: EstadoRespaldo
    tablas: int
    registros: int
    detalle: str | None = None
    id_usuario: int | None = None
    created_at: datetime


class RespaldoVerificacion(BaseModel):
    id_respaldo: int
    nombre: str
    existe: bool
    checksum_actual: str | None = None
    checksum_registrado: str | None = None
    integro: bool
    mensaje: str


# --------------------------------------------------------------------------- #
# integraciones · HU-20
# --------------------------------------------------------------------------- #
class IntegracionEstado(BaseModel):
    servicio: str
    descripcion: str
    estado: str
    configurado: bool
    detalle: str | None = None
    ultima_ejecucion: datetime | None = None


class RegistroIntegracionRead(ORMModel):
    id_registro: int
    servicio: str
    accion: str
    estado: str
    mensaje: str | None = None
    detalle: str | None = None
    created_at: datetime


class ResultadoIntegracion(BaseModel):
    servicio: str
    accion: str
    estado: str
    mensaje: str
    detalle: dict | None = None
    ejecutado_en: datetime


class ActualizacionTiposCambio(BaseModel):
    actualizados: int
    fuente: str
    fecha: date
    tasas: dict[str, float]
    modo: str = Field(description="servicio | respaldo local")


class EnvioCorreo(BaseModel):
    """Cuerpo de la prueba de la integración de correo."""

    destinatario: str = Field(min_length=5, max_length=150)
    asunto: str = Field(default="Prueba de integración RiTech", max_length=200)
    mensaje: str = Field(default="Mensaje de prueba del sistema RiTech.", max_length=2000)

    @model_validator(mode="after")
    def _correo_valido(self) -> "EnvioCorreo":
        if "@" not in self.destinatario:
            raise ValueError("El destinatario debe ser una dirección de correo")
        return self
