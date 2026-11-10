"""Las nueve tablas del modelo de datos de RiTech SAS.

Transcripción literal de *RiTech_Base_datos_relaciones_equipo_APIs.pdf*:

    usuarios · clientes · productos · fincas · lotes
    exportaciones · detalle_exportacion · documentos_exportacion · envios

y sus relaciones:

    fincas            → lotes                    (1:N)
    productos         → lotes                    (1:N)
    clientes          → exportaciones            (1:N)
    usuarios          → exportaciones            (1:N)
    exportaciones     → detalle_exportacion      (1:N)
    lotes             → detalle_exportacion      (1:N)
    exportaciones     → documentos_exportacion   (1:N)
    exportaciones     → envios                   (1:N)

Los tipos son portables entre PostgreSQL, MySQL y SQLite. El motor de
producción es PostgreSQL (RR-003).
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import (
    EstadoCalidad,
    EstadoDocumento,
    EstadoEnvio,
    EstadoExportacion,
    Rol,
    TipoDocumento,
    TipoProducto,
    enum_col,
)


# --------------------------------------------------------------------------- #
# 1. usuarios
# --------------------------------------------------------------------------- #
class Usuario(Base):
    __tablename__ = "usuarios"

    id_usuario: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    correo: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    contrasena_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[Rol] = mapped_column(enum_col(Rol), nullable=False, default=Rol.ADMINISTRADOR)

    # A qué empresa pertenece la cuenta. Solo se usa cuando el rol es
    # «Cliente europeo»: es lo que permite que el portal muestre únicamente las
    # exportaciones y los envíos de esa empresa, y no los de las demás.
    # Para el personal de RiTech queda en NULL.
    id_cliente: Mapped[int | None] = mapped_column(
        ForeignKey("clientes.id_cliente", ondelete="RESTRICT"), nullable=True
    )

    # Extensiones necesarias para HU-02 (sesión segura) y HU-21 (auditoría).
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="activo")
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    ultimo_acceso: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    exportaciones: Mapped[list[Exportacion]] = relationship(back_populates="usuario")

    #: La empresa de la que es contacto. Es el lado «hijo» de la relación: la
    #: lista de contactos vive en `Cliente.usuarios`. Para el personal de RiTech
    #: queda en NULL, porque no pertenece a ninguna empresa compradora.
    cliente: Mapped[Cliente | None] = relationship(back_populates="usuarios")

    __table_args__ = (
        Index("ix_usuarios_rol", "rol"),
        Index("ix_usuarios_cliente", "id_cliente"),
    )


# --------------------------------------------------------------------------- #
# 2. clientes  (clientes importadores de la Unión Europea)
# --------------------------------------------------------------------------- #
class Cliente(Base):
    __tablename__ = "clientes"

    id_cliente: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre_empresa: Mapped[str] = mapped_column(String(150), nullable=False)
    pais: Mapped[str] = mapped_column(String(100), nullable=False)
    direccion: Mapped[str | None] = mapped_column(String(200), nullable=True)
    correo: Mapped[str | None] = mapped_column(String(150), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # Extensiones para el módulo comercial (Informe §6.5) y el portal UE.
    contacto: Mapped[str | None] = mapped_column(String(150), nullable=True)
    vat: Mapped[str | None] = mapped_column(String(50), nullable=True)
    moneda_preferida: Mapped[str] = mapped_column(String(10), nullable=False, default="EUR")
    puerto_destino: Mapped[str | None] = mapped_column(String(100), nullable=True)
    activo: Mapped[bool] = mapped_column(nullable=False, default=True)

    exportaciones: Mapped[list[Exportacion]] = relationship(
        back_populates="cliente", cascade="all, delete-orphan"
    )

    #: Cuentas de acceso de los contactos de este cliente (HU-10, portal UE).
    #: `Usuario` se declara antes que `Cliente` en el archivo, pero con
    #: `from __future__ import annotations` la referencia es texto y SQLAlchemy la
    #: resuelve al montar los metadatos.
    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="cliente")

    __table_args__ = (Index("ix_clientes_pais", "pais"),)


# --------------------------------------------------------------------------- #
# 3. productos
# --------------------------------------------------------------------------- #
class Producto(Base):
    __tablename__ = "productos"

    id_producto: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo: Mapped[TipoProducto] = mapped_column(enum_col(TipoProducto), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Extensiones comerciales: variedad, unidad de medida y precio de referencia.
    variedad: Mapped[str | None] = mapped_column(String(100), nullable=True)
    unidad_medida: Mapped[str] = mapped_column(String(20), nullable=False, default="kg")
    precio_referencia_eur: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    activo: Mapped[bool] = mapped_column(nullable=False, default=True)

    lotes: Mapped[list[Lote]] = relationship(back_populates="producto")

    __table_args__ = (Index("ix_productos_tipo", "tipo"),)


# --------------------------------------------------------------------------- #
# 4. fincas
# --------------------------------------------------------------------------- #
class Finca(Base):
    __tablename__ = "fincas"

    id_finca: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    ubicacion: Mapped[str] = mapped_column(String(200), nullable=False)
    departamento: Mapped[str] = mapped_column(String(100), nullable=False)
    propietario: Mapped[str] = mapped_column(String(150), nullable=False)

    # Extensiones del módulo de productores (Informe §6.2) y EUDR.
    productor: Mapped[str | None] = mapped_column(String(150), nullable=True)
    asociacion: Mapped[str | None] = mapped_column(String(150), nullable=True)
    altura_msnm: Mapped[int | None] = mapped_column(nullable=True)
    superficie_ha: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    capacidad_produccion_kg: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    latitud: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitud: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)

    lotes: Mapped[list[Lote]] = relationship(
        back_populates="finca", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_fincas_departamento", "departamento"),)


# --------------------------------------------------------------------------- #
# 5. lotes
# --------------------------------------------------------------------------- #
class Lote(Base):
    __tablename__ = "lotes"

    id_lote: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_finca: Mapped[int] = mapped_column(
        ForeignKey("fincas.id_finca", ondelete="CASCADE"), nullable=False
    )
    id_producto: Mapped[int] = mapped_column(
        ForeignKey("productos.id_producto", ondelete="RESTRICT"), nullable=False
    )
    codigo_lote: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    cantidad_kg: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    fecha_cosecha: Mapped[date] = mapped_column(Date, nullable=False)
    estado_calidad: Mapped[EstadoCalidad] = mapped_column(
        enum_col(EstadoCalidad), nullable=False, default=EstadoCalidad.PENDIENTE
    )

    # Extensiones: reserva de inventario y consumo por exportación.
    disponible_kg: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    consumo_kg: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0")
    )
    variedad: Mapped[str | None] = mapped_column(String(100), nullable=True)
    altura_msnm: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    finca: Mapped[Finca] = relationship(back_populates="lotes")
    producto: Mapped[Producto] = relationship(back_populates="lotes")
    detalles: Mapped[list[DetalleExportacion]] = relationship(back_populates="lote")
    calidad: Mapped[CalidadLote | None] = relationship(
        back_populates="lote", cascade="all, delete-orphan", uselist=False
    )
    certificaciones: Mapped[list[Certificacion]] = relationship(
        back_populates="lote", cascade="all, delete-orphan"
    )
    eventos: Mapped[list[EventoTrazabilidad]] = relationship(
        back_populates="lote",
        cascade="all, delete-orphan",
        order_by="EventoTrazabilidad.fecha",
    )

    __table_args__ = (
        Index("ix_lotes_finca", "id_finca"),
        Index("ix_lotes_producto", "id_producto"),
        Index("ix_lotes_estado_calidad", "estado_calidad"),
    )


# --------------------------------------------------------------------------- #
# 6. exportaciones
# --------------------------------------------------------------------------- #
class Exportacion(Base):
    __tablename__ = "exportaciones"

    id_exportacion: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_cliente: Mapped[int] = mapped_column(
        ForeignKey("clientes.id_cliente", ondelete="RESTRICT"), nullable=False
    )
    id_usuario: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id_usuario", ondelete="RESTRICT"), nullable=False
    )
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    estado: Mapped[EstadoExportacion] = mapped_column(
        enum_col(EstadoExportacion), nullable=False, default=EstadoExportacion.PEDIDO_RECIBIDO
    )
    moneda: Mapped[str] = mapped_column(String(10), nullable=False, default="EUR")

    # Extensiones del módulo comercial.
    numero_contrato: Mapped[str | None] = mapped_column(String(60), nullable=True, unique=True)
    incoterm: Mapped[str | None] = mapped_column(String(20), nullable=True)
    puerto_origen: Mapped[str | None] = mapped_column(String(100), nullable=True)
    puerto_destino: Mapped[str | None] = mapped_column(String(100), nullable=True)
    valor_total: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=Decimal("0")
    )
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    cliente: Mapped[Cliente] = relationship(back_populates="exportaciones")
    usuario: Mapped[Usuario] = relationship(back_populates="exportaciones")
    detalles: Mapped[list[DetalleExportacion]] = relationship(
        back_populates="exportacion",
        cascade="all, delete-orphan",
        order_by="DetalleExportacion.id_detalle",
    )
    documentos: Mapped[list[DocumentoExportacion]] = relationship(
        back_populates="exportacion", cascade="all, delete-orphan"
    )
    envios: Mapped[list[Envio]] = relationship(back_populates="exportacion")

    __table_args__ = (
        Index("ix_exportaciones_cliente", "id_cliente"),
        Index("ix_exportaciones_usuario", "id_usuario"),
        Index("ix_exportaciones_estado", "estado"),
    )

    # ---properties---------------------------------------------------------- #
    @property
    def total_kg(self) -> Decimal:
        return sum((d.cantidad_kg for d in self.detalles), Decimal("0"))

    @property
    def valor_calculado(self) -> Decimal:
        return sum(
            (d.cantidad_kg * d.precio_kg for d in self.detalles), Decimal("0")
        )

    @property
    def dias_transito(self) -> int | None:
        fechas = [e.fecha_llegada for e in self.envios if e.fecha_llegada]
        salidas = [e.fecha_salida for e in self.envios if e.fecha_salida]
        if not fechas or not salidas:
            return None
        return (max(fechas) - min(salidas)).days


# --------------------------------------------------------------------------- #
# 7. detalle_exportacion
# --------------------------------------------------------------------------- #
class DetalleExportacion(Base):
    __tablename__ = "detalle_exportacion"

    id_detalle: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_exportacion: Mapped[int] = mapped_column(
        ForeignKey("exportaciones.id_exportacion", ondelete="CASCADE"), nullable=False
    )
    id_lote: Mapped[int] = mapped_column(
        ForeignKey("lotes.id_lote", ondelete="RESTRICT"), nullable=False
    )
    cantidad_kg: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    precio_kg: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    exportacion: Mapped[Exportacion] = relationship(back_populates="detalles")
    lote: Mapped[Lote] = relationship(back_populates="detalles")

    __table_args__ = (
        UniqueConstraint("id_exportacion", "id_lote", name="uq_detalle_exportacion_lote"),
        Index("ix_detalle_exportacion", "id_exportacion"),
    )

    @property
    def subtotal(self) -> Decimal:
        return self.cantidad_kg * self.precio_kg


# --------------------------------------------------------------------------- #
# 8. documentos_exportacion
# --------------------------------------------------------------------------- #
class DocumentoExportacion(Base):
    __tablename__ = "documentos_exportacion"

    id_documento: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_exportacion: Mapped[int] = mapped_column(
        ForeignKey("exportaciones.id_exportacion", ondelete="CASCADE"), nullable=False
    )
    tipo_documento: Mapped[TipoDocumento] = mapped_column(
        enum_col(TipoDocumento, 100), nullable=False
    )
    numero_documento: Mapped[str] = mapped_column(String(100), nullable=False)
    fecha_emision: Mapped[date] = mapped_column(Date, nullable=False)
    estado: Mapped[EstadoDocumento] = mapped_column(
        enum_col(EstadoDocumento), nullable=False, default=EstadoDocumento.BORRADOR
    )

    # Extensiones: referencia al archivo almacenado (S3/Azure/disco local).
    archivo: Mapped[str | None] = mapped_column(String(300), nullable=True)
    tamano_bytes: Mapped[int | None] = mapped_column(nullable=True)
    autorizado_cliente: Mapped[bool] = mapped_column(nullable=False, default=False)

    exportacion: Mapped[Exportacion] = relationship(back_populates="documentos")

    __table_args__ = (
        UniqueConstraint("numero_documento", name="uq_documento_numero"),
        Index("ix_documentos_exportacion", "id_exportacion"),
    )


# --------------------------------------------------------------------------- #
# 9. envios
# --------------------------------------------------------------------------- #
class Envio(Base):
    __tablename__ = "envios"

    id_envio: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_exportacion: Mapped[int] = mapped_column(
        ForeignKey("exportaciones.id_exportacion", ondelete="CASCADE"), nullable=False
    )
    transportadora: Mapped[str] = mapped_column(String(100), nullable=False)
    numero_seguimiento: Mapped[str] = mapped_column(String(100), nullable=False)
    fecha_salida: Mapped[date | None] = mapped_column(Date, nullable=True)
    fecha_llegada: Mapped[date | None] = mapped_column(Date, nullable=True)
    estado: Mapped[EstadoEnvio] = mapped_column(
        enum_col(EstadoEnvio), nullable=False, default=EstadoEnvio.PROGRAMADO
    )

    # Extensiones del módulo de logística (Informe §6.6).
    id_contenedor: Mapped[int | None] = mapped_column(
        ForeignKey("contenedores.id_contenedor", ondelete="SET NULL"), nullable=True
    )
    puerto_origen: Mapped[str | None] = mapped_column(String(100), nullable=True)
    puerto_destino: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tipo_transporte: Mapped[str] = mapped_column(
        String(20), nullable=False, default="Marítimo"
    )
    costo_flete: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    temperatura_c: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)

    exportacion: Mapped[Exportacion] = relationship(back_populates="envios")
    contenedor: Mapped[Contenedor | None] = relationship(back_populates="envios")

    __table_args__ = (
        UniqueConstraint("numero_seguimiento", name="uq_envio_seguimiento"),
        Index("ix_envios_exportacion", "id_exportacion"),
        Index("ix_envios_estado", "estado"),
    )


# --------------------------------------------------------------------------- #
# Imports diferidos para resolver las referencias de tipado entre tablas.
# --------------------------------------------------------------------------- #
from app.models.sprint2 import (  # noqa: E402
    CalidadLote,
    Certificacion,
    Contenedor,
    EventoTrazabilidad,
)
