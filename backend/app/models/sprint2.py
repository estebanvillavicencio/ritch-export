"""Tablas de extensión introducidas por los módulos del Sprint 2.

El documento de base de datos fija nueve tablas nuclear. Los módulos de
Productores/Lotes, Calidad, Comercial y Logística necesitan registrar datos que
no caben en esas nueve (resultados de laboratorio, certificaciones, hitos de
trazabilidad, cotizaciones y contenedores), por lo que se añaden como tablas
separadas — sin alterar ni el nombre ni las columnas del modelo original.

    calidad_lote          → módulo Calidad              (HU-17)
    certificaciones       → cumplimiento / ficha de lote (Informe §6.4)
    eventos_trazabilidad  → módulo Trazabilidad         (HU-06)
    cotizaciones          → módulo Comercial            (HU-08)
    contenedores          → módulo Logística            (HU-12)
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import (
    EstadoCotizacion,
    EstadoCertificacion,
    EtapaTrazabilidad,
    TipoCertificacion,
    enum_col,
)


# --------------------------------------------------------------------------- #
# calidad_lote — HU-17 · resultados de catación y laboratorio
# --------------------------------------------------------------------------- #
class CalidadLote(Base):
    __tablename__ = "calidad_lote"

    id_calidad: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_lote: Mapped[int] = mapped_column(
        ForeignKey("lotes.id_lote", ondelete="CASCADE"), nullable=False, unique=True
    )

    humedad: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    puntaje_cata: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    actividad_agua: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    granulometria: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    impurezas: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    cafeina_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    grasa_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    prueba_metodos: Mapped[str | None] = mapped_column(String(200), nullable=True)
    clasificacion: Mapped[str | None] = mapped_column(String(50), nullable=True)
    laboratorio: Mapped[str | None] = mapped_column(String(150), nullable=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    fecha_analisis: Mapped[date | None] = mapped_column(Date, nullable=True)
    aprobado_por: Mapped[str | None] = mapped_column(String(100), nullable=True)

    lote: Mapped["Lote"] = relationship(back_populates="calidad")  # type: ignore[name-defined]

    __table_args__ = (Index("ix_calidad_lote", "id_lote"),)


# --------------------------------------------------------------------------- #
# certificaciones — Informe §6.4 · EUDR, orgánico, Fairtrade, fitosanitario
# --------------------------------------------------------------------------- #
class Certificacion(Base):
    __tablename__ = "certificaciones"

    id_certificacion: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_lote: Mapped[int | None] = mapped_column(
        ForeignKey("lotes.id_lote", ondelete="CASCADE"), nullable=True
    )
    id_finca: Mapped[int | None] = mapped_column(
        ForeignKey("fincas.id_finca", ondelete="CASCADE"), nullable=True
    )

    tipo: Mapped[TipoCertificacion] = mapped_column(enum_col(TipoCertificacion), nullable=False)
    entidad_emisora: Mapped[str | None] = mapped_column(String(150), nullable=True)
    numero_certificado: Mapped[str | None] = mapped_column(String(100), nullable=True)
    fecha_emision: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_vencimiento: Mapped[date | None] = mapped_column(Date, nullable=True)
    archivo: Mapped[str | None] = mapped_column(String(300), nullable=True)
    lote_georreferenciado: Mapped[bool] = mapped_column(
        nullable=False, default=False, comment="EUDR: geolocalización del lote"
    )
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)

    lote: Mapped["Lote | None"] = relationship(back_populates="certificaciones")  # type: ignore[name-defined]

    __table_args__ = (
        Index("ix_certificaciones_lote", "id_lote"),
        Index("ix_certificaciones_finca", "id_finca"),
        Index("ix_certificaciones_vencimiento", "fecha_vencimiento"),
    )

    @property
    def dias_para_vencer(self) -> int | None:
        if self.fecha_vencimiento is None:
            return None
        return (self.fecha_vencimiento - date.today()).days


# --------------------------------------------------------------------------- #
# eventos_trazabilidad — HU-06 · recorrido del lote finca → destino
# --------------------------------------------------------------------------- #
class EventoTrazabilidad(Base):
    __tablename__ = "eventos_trazabilidad"

    id_evento: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_lote: Mapped[int] = mapped_column(
        ForeignKey("lotes.id_lote", ondelete="CASCADE"), nullable=False
    )
    etapa: Mapped[EtapaTrazabilidad] = mapped_column(
        enum_col(EtapaTrazabilidad), nullable=False
    )
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    ubicacion: Mapped[str | None] = mapped_column(String(150), nullable=True)
    descripcion: Mapped[str | None] = mapped_column(String(300), nullable=True)
    documento: Mapped[str | None] = mapped_column(String(300), nullable=True)
    id_envio: Mapped[int | None] = mapped_column(
        ForeignKey("envios.id_envio", ondelete="SET NULL"), nullable=True
    )

    lote: Mapped["Lote"] = relationship(back_populates="eventos")  # type: ignore[name-defined]

    __table_args__ = (
        Index("ix_eventos_lote", "id_lote"),
        Index("ix_eventos_etapa", "etapa"),
    )


# --------------------------------------------------------------------------- #
# cotizaciones — HU-08 · cotizaciones y contratos en distintas monedas
# --------------------------------------------------------------------------- #
class Cotizacion(Base):
    __tablename__ = "cotizaciones"

    id_cotizacion: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    numero: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    id_cliente: Mapped[int] = mapped_column(
        ForeignKey("clientes.id_cliente", ondelete="CASCADE"), nullable=False
    )
    id_usuario: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id_usuario", ondelete="RESTRICT"), nullable=False
    )
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    validez_dias: Mapped[int] = mapped_column(nullable=False, default=15)
    moneda: Mapped[str] = mapped_column(String(10), nullable=False, default="EUR")
    incoterm: Mapped[str] = mapped_column(String(20), nullable=False, default="FOB")
    estado: Mapped[EstadoCotizacion] = mapped_column(
        enum_col(EstadoCotizacion, 30), nullable=False, default=EstadoCotizacion.BORRADOR
    )
    precio_kg: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    cantidad_kg: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    puerto_origen: Mapped[str | None] = mapped_column(String(100), nullable=True)
    puerto_destino: Mapped[str | None] = mapped_column(String(100), nullable=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    id_exportacion: Mapped[int | None] = mapped_column(
        ForeignKey("exportaciones.id_exportacion", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    cliente: Mapped["Cliente"] = relationship()  # type: ignore[name-defined]
    usuario: Mapped["Usuario"] = relationship()  # type: ignore[name-defined]

    __table_args__ = (
        Index("ix_cotizaciones_cliente", "id_cliente"),
        Index("ix_cotizaciones_estado", "estado"),
    )

    @property
    def valor_total(self) -> Decimal:
        return self.precio_kg * self.cantidad_kg


# --------------------------------------------------------------------------- #
# solicitudes_pedido · pedidos iniciados por el comprador desde el portal
# --------------------------------------------------------------------------- #
class SolicitudPedido(Base):
    __tablename__ = "solicitudes_pedido"

    id_solicitud: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_cliente: Mapped[int] = mapped_column(
        ForeignKey("clientes.id_cliente", ondelete="CASCADE"), nullable=False
    )
    id_usuario: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id_usuario", ondelete="RESTRICT"), nullable=False
    )
    id_producto: Mapped[int] = mapped_column(
        ForeignKey("productos.id_producto", ondelete="RESTRICT"), nullable=False
    )
    cantidad_kg: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    incoterm: Mapped[str] = mapped_column(String(20), nullable=False, default="FOB")
    puerto_destino: Mapped[str | None] = mapped_column(String(100), nullable=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default="Pendiente")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    cliente: Mapped["Cliente"] = relationship()
    producto: Mapped["Producto"] = relationship()
    usuario: Mapped["Usuario"] = relationship()

    __table_args__ = (
        Index("ix_solicitudes_pedido_cliente", "id_cliente"),
        Index("ix_solicitudes_pedido_estado", "estado"),
    )


# --------------------------------------------------------------------------- #
# contenedores — módulo de logística (HU-12)
# --------------------------------------------------------------------------- #
class Contenedor(Base):
    __tablename__ = "contenedores"

    id_contenedor: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    tipo: Mapped[str] = mapped_column(String(10), nullable=False, default="20GP")
    capacidad_kg: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    naviera: Mapped[str | None] = mapped_column(String(100), nullable=True)
    disponible: Mapped[bool] = mapped_column(nullable=False, default=True)

    envios: Mapped[list["Envio"]] = relationship(back_populates="contenedor")  # type: ignore[name-defined]

    __table_args__ = (Index("ix_contenedores_disponible", "disponible"),)
