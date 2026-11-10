"""Esquemas del panel general y los reportes (Informe §6.10 · HU-15)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import EstadoExportacion, TipoProducto
from app.schemas.catalogos import CertificacionResumida
from app.schemas.common import ResumenTarjeta


class CumplimientoNormativo(BaseModel):
    """Barras de cumplimiento del panel general."""

    normativa: str
    porcentaje: int = Field(ge=0, le=100)
    detalle: str | None = None
    vencen_pronto: int = 0


class PedidoReciente(BaseModel):
    """Fila de la tabla «Pedidos recientes» del panel."""

    id_exportacion: int
    cliente: str
    cliente_pais: str
    producto: str
    tipo_producto: TipoProducto | None = None
    cantidad_kg: float
    estado: EstadoExportacion
    valor: float
    moneda: str
    puerto_destino: str | None = None


class FichaLote(BaseModel):
    """Elemento «Ficha de lote» del panel: el ticket con troquel."""

    id_lote: int
    codigo_lote: str
    finca: str
    ubicacion: str
    altura_msnm: int | None = None
    variedad: str | None = None
    producto: str
    tipo_producto: TipoProducto | None = None
    peso_kg: float
    disponible_kg: float
    fecha_cosecha: date
    estado_calidad: str
    certificaciones: list[CertificacionResumida] = Field(default_factory=list)
    verificado: bool = False


class LineaTiempoEnvio(BaseModel):
    """Etapas del envío mostradas en la línea de tiempo del panel."""

    id_envio: int
    etiqueta: str
    transporte: str
    numero_seguimiento: str
    puerto_origen: str | None = None
    puerto_destino: str | None = None
    fecha_salida: date | None = None
    fecha_llegada: date | None = None
    estado: str
    etapas: list[dict] = Field(default_factory=list)


class DashboardRead(BaseModel):
    """Respuesta completa del panel general."""

    tarjetas: list[ResumenTarjeta]
    cumplimiento: list[CumplimientoNormativo]
    pedidos_recientes: list[PedidoReciente]
    ficha_lote: FichaLote | None = None
    envio_destacado: LineaTiempoEnvio | None = None
    alertas: list[dict] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# KPIs consolidados
# --------------------------------------------------------------------------- #
class KpiVolumenProducto(BaseModel):
    tipo: TipoProducto
    kilos: float
    porcentaje: float


class KpiPaisDestino(BaseModel):
    pais: str
    kilos: float
    valor: float
    exportaciones: int


class KpiCliente(BaseModel):
    cliente: str
    pais: str
    exportaciones: int
    valor: float


class KpiContrato(BaseModel):
    estado: EstadoExportacion
    count: int
    valor: float


class KpiResumen(BaseModel):
    """Indicadores del módulo de reportes y KPIs."""

    volumen_total_kg: float
    kilos_cafe: float
    kilos_cacao: float
    ingresos_totales: float
    ingresos_por_moneda: dict[str, float]
    pedidos: int
    envios_activos: int
    clientes_activos: int
    tiempo_promedio_entrega_dias: float | None
    pagos_pendientes: float
    por_producto: list[KpiVolumenProducto]
    por_pais: list[KpiPaisDestino]
    por_cliente: list[KpiCliente]
    por_estado: list[KpiContrato]
    certificaciones_por_renovar: int
    lotes_pendientes_calidad: int


class ResumenInventario(BaseModel):
    """HU-05 · control de inventario disponible para exportación."""

    kilos_totales: float
    kilos_disponibles: float
    kilos_comprometidos: float
    lotes: int
    por_tipo: list[KpiVolumenProducto]
