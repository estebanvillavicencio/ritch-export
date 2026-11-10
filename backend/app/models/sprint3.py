"""Tablas de los módulos del Sprint 3 y del Sprint 4.

Sprint 3 — financiero, notificaciones y auditoría:

    pagos                  → HU-14 · anticipos, pagos, saldos y cartas de crédito
    notificaciones         → HU-16 · avisos de vencimientos y cambios de estado
    auditoria              → HU-21 · registro de las acciones críticas

Sprint 4 — integraciones, multimoneda y continuidad:

    tipos_cambio           → HU-19 · conversión de precios a EUR/USD/COP
    respaldos              → HU-22 · copias de seguridad verificables
    registros_integracion  → HU-20 · bitácora de los servicios externos

Igual que las extensiones del Sprint 2, son tablas nuevas: no se altera
ninguna de las nueve tablas del modelo de datos original.
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
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import (
    EstadoPago,
    EstadoRespaldo,
    MetodoPago,
    TipoNotificacion,
    TipoPago,
    TipoRespaldo,
    enum_col,
)


# --------------------------------------------------------------------------- #
# pagos — HU-14 · anticipos, pagos, saldos y cartas de crédito
# --------------------------------------------------------------------------- #
class Pago(Base):
    __tablename__ = "pagos"

    id_pago: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_exportacion: Mapped[int] = mapped_column(
        ForeignKey("exportaciones.id_exportacion", ondelete="CASCADE"), nullable=False
    )
    id_usuario: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id_usuario", ondelete="RESTRICT"), nullable=False
    )

    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    tipo: Mapped[TipoPago] = mapped_column(enum_col(TipoPago), nullable=False)
    metodo: Mapped[MetodoPago] = mapped_column(
        enum_col(MetodoPago), nullable=False, default=MetodoPago.TRANSFERENCIA
    )
    estado: Mapped[EstadoPago] = mapped_column(
        enum_col(EstadoPago), nullable=False, default=EstadoPago.REGISTRADO
    )
    valor: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    moneda: Mapped[str] = mapped_column(String(10), nullable=False, default="EUR")

    referencia: Mapped[str | None] = mapped_column(String(100), nullable=True)
    banco: Mapped[str | None] = mapped_column(String(150), nullable=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    exportacion: Mapped["Exportacion"] = relationship()  # type: ignore[name-defined]
    usuario: Mapped["Usuario"] = relationship()  # type: ignore[name-defined]

    __table_args__ = (
        Index("ix_pagos_exportacion", "id_exportacion"),
        Index("ix_pagos_estado", "estado"),
        Index("ix_pagos_fecha", "fecha"),
    )


# --------------------------------------------------------------------------- #
# notificaciones — HU-16 · bandeja de avisos del sistema
# --------------------------------------------------------------------------- #
class Notificacion(Base):
    __tablename__ = "notificaciones"

    id_notificacion: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Dos formas de destinar un aviso: a una cuenta concreta o a todo un rol.
    # El personal interno ve las de su rol y las globales (`rol_destino` nulo).
    id_usuario: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id_usuario", ondelete="CASCADE"), nullable=True
    )
    rol_destino: Mapped[str | None] = mapped_column(String(50), nullable=True)

    tipo: Mapped[TipoNotificacion] = mapped_column(
        enum_col(TipoNotificacion), nullable=False, default=TipoNotificacion.SISTEMA
    )
    tono: Mapped[str] = mapped_column(String(20), nullable=False, default="azul")
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    detalle: Mapped[str | None] = mapped_column(Text, nullable=True)
    enlace: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Clave estable del hecho que originó el aviso. Permite sincronizar sin
    # duplicar: dos ejecuciones del mismo vencimiento dejan una sola fila.
    clave: Mapped[str | None] = mapped_column(String(160), nullable=True, unique=True)
    leida: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    fecha: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    usuario: Mapped["Usuario | None"] = relationship()  # type: ignore[name-defined]

    __table_args__ = (
        Index("ix_notificaciones_usuario", "id_usuario"),
        Index("ix_notificaciones_rol", "rol_destino"),
        Index("ix_notificaciones_leida", "leida"),
        Index("ix_notificaciones_fecha", "fecha"),
    )


# --------------------------------------------------------------------------- #
# auditoria — HU-21 · acciones críticas del sistema
# --------------------------------------------------------------------------- #
class Auditoria(Base):
    __tablename__ = "auditoria"

    id_auditoria: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_usuario: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id_usuario", ondelete="SET NULL"), nullable=True
    )
    # Se guarda el correo además de la FK: si la cuenta se elimina, el rastro
    # sigue diciendo quién hizo la operación.
    usuario_correo: Mapped[str | None] = mapped_column(String(150), nullable=True)

    accion: Mapped[str] = mapped_column(String(100), nullable=False)
    entidad: Mapped[str | None] = mapped_column(String(80), nullable=True)
    id_entidad: Mapped[str | None] = mapped_column(String(50), nullable=True)
    detalle: Mapped[str | None] = mapped_column(Text, nullable=True)

    metodo: Mapped[str | None] = mapped_column(String(10), nullable=True)
    ruta: Mapped[str | None] = mapped_column(String(300), nullable=True)
    estado_http: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ip: Mapped[str | None] = mapped_column(String(60), nullable=True)
    fecha: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    usuario: Mapped["Usuario | None"] = relationship()  # type: ignore[name-defined]

    __table_args__ = (
        Index("ix_auditoria_usuario", "id_usuario"),
        Index("ix_auditoria_fecha", "fecha"),
        Index("ix_auditoria_entidad", "entidad"),
    )


# --------------------------------------------------------------------------- #
# tipos_cambio — HU-19 · multimoneda
# --------------------------------------------------------------------------- #
class TipoCambio(Base):
    """Tasa de una moneda contra el euro.

    ``tasa`` son las unidades de la moneda que equivalen a 1 EUR:
    1 EUR = 1,09 USD → ``moneda='USD'``, ``tasa=1.09``.
    """

    __tablename__ = "tipos_cambio"

    id_tipo_cambio: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    moneda: Mapped[str] = mapped_column(String(10), nullable=False)
    tasa: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    fuente: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("moneda", "fecha", name="uq_tipo_cambio_moneda_fecha"),
        Index("ix_tipos_cambio_fecha", "fecha"),
    )


# --------------------------------------------------------------------------- #
# respaldos — HU-22 · copias de seguridad
# --------------------------------------------------------------------------- #
class Respaldo(Base):
    __tablename__ = "respaldos"

    id_respaldo: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    ruta: Mapped[str] = mapped_column(String(400), nullable=False)
    tamano_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tipo: Mapped[TipoRespaldo] = mapped_column(
        enum_col(TipoRespaldo), nullable=False, default=TipoRespaldo.MANUAL
    )
    estado: Mapped[EstadoRespaldo] = mapped_column(
        enum_col(EstadoRespaldo), nullable=False, default=EstadoRespaldo.COMPLETADO
    )
    tablas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    registros: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    detalle: Mapped[str | None] = mapped_column(Text, nullable=True)
    id_usuario: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id_usuario", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    usuario: Mapped["Usuario | None"] = relationship()  # type: ignore[name-defined]

    __table_args__ = (Index("ix_respaldos_fecha", "created_at"),)


# --------------------------------------------------------------------------- #
# registros_integracion — HU-20 · bitácora de servicios externos
# --------------------------------------------------------------------------- #
class RegistroIntegracion(Base):
    __tablename__ = "registros_integracion"

    id_registro: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    servicio: Mapped[str] = mapped_column(String(60), nullable=False)
    accion: Mapped[str] = mapped_column(String(100), nullable=False)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default="ok")
    mensaje: Mapped[str | None] = mapped_column(Text, nullable=True)
    detalle: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("ix_registros_integracion_servicio", "servicio"),
        Index("ix_registros_integracion_fecha", "created_at"),
    )
