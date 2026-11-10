"""Reglas de negocio transversales.

 concentrate la lógica que varios módulos comparten:

* generación de códigos correlativos (lotes, contratos, cotizaciones);
* cálculo de disponibilidad de inventario (HU-05);
* transiciones válidas de estado de una exportación (Informe §6.9);
* estado derivado de una certificación (Informe §6.4);
* línea de tiempo de trazabilidad de un envío (HU-06 / mockup).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    CalidadLote,
    Certificacion,
    DetalleExportacion,
    Envio,
    EstadoCertificacion,
    EstadoEnvio,
    EstadoExportacion,
    Exportacion,
    Lote,
    ORDEN_EXPORTACION,
    ORDEN_TRAZABILIDAD,
    Producto,
    EtapaTrazabilidad,
)

#: Días de margen para marcar una certificación como «por renovar».
DIAS_RENOVACION = 45


# --------------------------------------------------------------------------- #
# Códigos correlativos
# --------------------------------------------------------------------------- #
def _siguiente_correlativo(db: Session, modelo, columna, prefijo: str) -> str:
    """Genera el siguiente código ``PREFIJO-AAAA-NNNN`` del año en curso.

    El correlativo se calcula en Python para no depender de funciones de
    cadenas específicas del motor (substr en PostgreSQL, left en MySQL…).
    """
    anio = date.today().year
    patron = f"{prefijo}-{anio}-"
    existentes = db.scalars(
        select(columna).where(columna.like(f"{patron}%"))
    ).all()

    consecutivo = 1
    for codigo in existentes:
        try:
            consecutivo = max(consecutivo, int(str(codigo).rsplit("-", 1)[1]) + 1)
        except (IndexError, ValueError):
            continue
    return f"{patron}{consecutivo:04d}"


def generar_codigo_lote(db: Session) -> str:
    """Código de lote con el formato del mockup: ``CO-HUI-2026-0912``."""
    return _siguiente_correlativo(db, Lote, Lote.codigo_lote, "CO-HUI")


def generar_numero_contrato(db: Session) -> str:
    return _siguiente_correlativo(db, Exportacion, Exportacion.numero_contrato, "CT")


def generar_numero_cotizacion(db: Session) -> str:
    from app.models import Cotizacion

    return _siguiente_correlativo(db, Cotizacion, Cotizacion.numero, "QT")


# --------------------------------------------------------------------------- #
# Inventario (HU-05)
# --------------------------------------------------------------------------- #
def recalcular_disponibles(db: Session) -> None:
    """Fija ``disponible_kg`` de cada lote según lo ya comprometido.

    ``disponible_kg = cantidad_kg - Σ cantidad_kg de los detalles de exportación``
    """
    comprometido = dict(
        db.execute(
            select(DetalleExportacion.id_lote, func.sum(DetalleExportacion.cantidad_kg))
            .join(
                Exportacion,
                Exportacion.id_exportacion == DetalleExportacion.id_exportacion,
            )
            .where(Exportacion.estado != EstadoExportacion.ANULADO)
            .group_by(DetalleExportacion.id_lote)
        ).all()
    )

    for lote in db.scalars(select(Lote)).all():
        usado = comprometido.get(lote.id_lote, Decimal("0"))
        lote.consumo_kg = usado
        lote.disponible_kg = max(Decimal("0"), lote.cantidad_kg - usado)
    db.flush()


def verificar_disponibilidad(db: Session, id_lote: int, cantidad: Decimal) -> None:
    """Lanza ``ValueError`` si el lote no tiene saldo suficiente."""
    lote = db.get(Lote, id_lote)
    if lote is None:
        raise ValueError(f"El lote {id_lote} no existe")
    disponible = lote.disponible_kg
    if disponible is None:
        disponible = lote.cantidad_kg - lote.consumo_kg
    if cantidad > disponible:
        raise ValueError(
            f"El lote {lote.codigo_lote} solo tiene {disponible} kg disponibles "
            f"y se solicitan {cantidad} kg"
        )


# --------------------------------------------------------------------------- #
# Estados de exportación (Informe §6.9)
# --------------------------------------------------------------------------- #
def puede_transicionar(actual: EstadoExportacion, nuevo: EstadoExportacion) -> bool:
    """Indica si el cambio de estado respeta la cadena de entrega.

    Se permite avanzar, retroceder un paso y anular desde cualquier estado
    previo a la entrega.
    """
    if actual == nuevo:
        return True
    if nuevo == EstadoExportacion.ANULADO:
        return actual in (
            EstadoExportacion.PEDIDO_RECIBIDO,
            EstadoExportacion.EN_PREPARACION,
            EstadoExportacion.EN_PRODUCCION,
        )
    if actual == EstadoExportacion.ANULADO:
        return False
    if actual not in ORDEN_EXPORTACION or nuevo not in ORDEN_EXPORTACION:
        return True
    distancia = abs(
        ORDEN_EXPORTACION.index(nuevo) - ORDEN_EXPORTACION.index(actual)
    )
    return distancia <= 1


def progreso(estado: EstadoExportacion) -> int:
    """Porcentaje de avance según la posición en la cadena de estados."""
    if estado == EstadoExportacion.ANULADO:
        return 0
    try:
        return round(
            (ORDEN_EXPORTACION.index(estado) + 1) / len(ORDEN_EXPORTACION) * 100
        )
    except ValueError:
        return 0


def siguiente_estado(estado: EstadoExportacion) -> EstadoExportacion | None:
    """Estado siguiente en la cadena, o ``None`` si ya está entregado."""
    try:
        indice = ORDEN_EXPORTACION.index(estado)
    except ValueError:
        return None
    if indice + 1 >= len(ORDEN_EXPORTACION):
        return None
    return ORDEN_EXPORTACION[indice + 1]


# --------------------------------------------------------------------------- #
# Certificaciones (Informe §6.4)
# --------------------------------------------------------------------------- #
def estado_certificacion(cert: Certificacion, hoy: date | None = None) -> EstadoCertificacion:
    """Deriva el estado de una certificación a partir de sus fechas."""
    hoy = hoy or date.today()
    if cert.fecha_emision > hoy:
        return EstadoCertificacion.PENDIENTE
    if cert.fecha_vencimiento is None:
        return EstadoCertificacion.VIGENTE
    if cert.fecha_vencimiento < hoy:
        return EstadoCertificacion.VENCIDA
    if (cert.fecha_vencimiento - hoy).days <= DIAS_RENOVACION:
        return EstadoCertificacion.POR_RENOVAR
    return EstadoCertificacion.VIGENTE


def cumple_eudr(cert: Certificacion) -> bool:
    """El Reglamento europeo de deforestación exige georreferenciación del lote."""
    if cert.tipo.value != "EUDR":
        return False
    return cert.lote_georreferenciado and estado_certificacion(cert) in (
        EstadoCertificacion.VIGENTE,
        EstadoCertificacion.POR_RENOVAR,
    )


# --------------------------------------------------------------------------- #
# Línea de tiempo de trazabilidad (mockup del panel)
# --------------------------------------------------------------------------- #
def linea_tiempo_envio(envio: Envio) -> list[dict]:
    """Construye las seis etapas de la línea de tiempo para un envío.

    Es la misma secuencia del mockup: Finca · Beneficio · Puerto origen ·
    Tránsito marítimo · Aduana UE · Cliente.
    """
    hoy = date.today()

    orden_estados = {
        EstadoEnvio.PROGRAMADO: 0,
        EstadoEnvio.EN_TRANSITO: 2,
        EstadoEnvio.EN_ADUANA: 3,
        EstadoEnvio.EN_DESTINO: 4,
        EstadoEnvio.ENTREGADO: 5,
        EstadoEnvio.DEMORADO: 2,
        EstadoEnvio.INCIDENCIA: 2,
    }
    indice_actual = orden_estados.get(envio.estado, 0)

    en_puerto = envio.fecha_salida is not None and envio.fecha_salida <= hoy
    estimado = envio.fecha_llegada

    etapas: list[dict] = []
    # Un envío entregado tiene el recorrido completo: no queda etapa «actual».
    entregado = envio.estado == EstadoEnvio.ENTREGADO
    for i, etapa in enumerate(ORDEN_TRAZABILIDAD):
        if entregado or i < indice_actual:
            estado = "done"
        elif i == indice_actual:
            estado = "current"
        else:
            estado = "pending"

        fecha = None
        ubicacion = None
        if etapa == EtapaTrazabilidad.PUERTO_ORIGEN and en_puerto:
            fecha = envio.fecha_salida
            ubicacion = envio.puerto_origen
        elif etapa == EtapaTrazabilidad.TRANSITO_MARITIMO and envio.fecha_salida:
            fecha = envio.fecha_salida
            ubicacion = envio.puerto_origen
        elif etapa == EtapaTrazabilidad.ADUANA_UE and envio.estado in (
            EstadoEnvio.EN_ADUANA,
            EstadoEnvio.EN_DESTINO,
            EstadoEnvio.ENTREGADO,
        ):
            fecha = estimado
            ubicacion = envio.puerto_destino
        elif etapa == EtapaTrazabilidad.CLIENTE and envio.fecha_llegada:
            fecha = envio.fecha_llegada
            ubicacion = envio.puerto_destino

        etapas.append(
            {
                "etapa": etapa.value,
                "estado": estado,
                "fecha": fecha,
                "ubicacion": ubicacion,
            }
        )
    return etapas


def dias_transito_previstos(envio: Envio) -> int | None:
    """Días estimados de tránsito entre salida y llegada."""
    if envio.fecha_salida and envio.fecha_llegada:
        return (envio.fecha_llegada - envio.fecha_salida).days
    return None


def fecha_salida_por_defecto() -> date:
    return date.today()


def fecha_llegada_estimada(dias: int = 28) -> date:
    """Tránsito marítimo típico Colombia → Europa del Norte."""
    return date.today() + timedelta(days=dias)


def ahora() -> datetime:
    return datetime.now()
