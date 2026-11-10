"""Indicadores, KPIs y agregados del panel general (Informe §6.10 · HU-15)."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Certificacion,
    Cliente,
    DetalleExportacion,
    Envio,
    EstadoCertificacion,
    EstadoEnvio,
    EstadoExportacion,
    Exportacion,
    Lote,
    Producto,
    Rol,
    TipoCertificacion,
    TipoProducto,
    Usuario,
)
from app.schemas.common import ResumenTarjeta
from app.schemas.panel import (
    CumplimientoNormativo,
    FichaLote,
    KpiCliente,
    KpiContrato,
    KpiPaisDestino,
    KpiResumen,
    KpiVolumenProducto,
    LineaTiempoEnvio,
    PedidoReciente,
    ResumenInventario,
)
from app.services.reglas import (
    DIAS_RENOVACION,
    estado_certificacion,
    linea_tiempo_envio,
    recalcular_disponibles,
)


def _sin_anuladas():
    return Exportacion.estado != EstadoExportacion.ANULADO


# --------------------------------------------------------------------------- #
# KPIs consolidados
# --------------------------------------------------------------------------- #
def calcular_kpis(db: Session) -> KpiResumen:
    """Calcula todos los indicadores gerenciales del sistema."""
    base = db.execute(
        select(
            func.coalesce(func.sum(DetalleExportacion.cantidad_kg), 0),
            func.count(func.distinct(Exportacion.id_exportacion)),
        )
        .select_from(DetalleExportacion)
        .join(Exportacion, Exportacion.id_exportacion == DetalleExportacion.id_exportacion)
        .join(Lote, Lote.id_lote == DetalleExportacion.id_lote)
        .join(Producto, Producto.id_producto == Lote.id_producto)
        .where(_sin_anuladas())
    ).one()

    volumen_total = Decimal(str(base[0] or 0))
    num_pedidos = int(base[1] or 0)

    # Volumen por tipo de producto (Informe §6.10: café vs. cacao)
    filas_tipo = db.execute(
        select(
            Producto.tipo,
            func.coalesce(func.sum(DetalleExportacion.cantidad_kg), 0),
        )
        .select_from(DetalleExportacion)
        .join(Exportacion, Exportacion.id_exportacion == DetalleExportacion.id_exportacion)
        .join(Lote, Lote.id_lote == DetalleExportacion.id_lote)
        .join(Producto, Producto.id_producto == Lote.id_producto)
        .where(_sin_anuladas())
        .group_by(Producto.tipo)
    ).all()

    por_producto: list[KpiVolumenProducto] = []
    kilos_cafe = kilos_cacao = Decimal("0")
    for tipo, kilos in filas_tipo:
        kilos = Decimal(str(kilos or 0))
        if tipo == TipoProducto.CAFE:
            kilos_cafe = kilos
        elif tipo == TipoProducto.CACAO:
            kilos_cacao = kilos
        por_producto.append(
            KpiVolumenProducto(
                tipo=tipo,
                kilos=float(kilos),
                porcentaje=float(round(kilos / volumen_total * 100, 1))
                if volumen_total
                else 0.0,
            )
        )

    # Ingresos por moneda (multimoneda, HU-19)
    ingresos = db.execute(
        select(
            Exportacion.moneda,
            func.coalesce(func.sum(DetalleExportacion.cantidad_kg * DetalleExportacion.precio_kg), 0),
        )
        .select_from(DetalleExportacion)
        .join(Exportacion, Exportacion.id_exportacion == DetalleExportacion.id_exportacion)
        .where(_sin_anuladas())
        .group_by(Exportacion.moneda)
    ).all()
    ingresos_por_moneda = {m: float(round(Decimal(str(v or 0)), 2)) for m, v in ingresos}

    # Países de destino
    por_pais = [
        KpiPaisDestino(
            pais=pais,
            kilos=float(kilos or 0),
            valor=float(round(Decimal(str(valor or 0)), 2)),
            exportaciones=int(num),
        )
        for pais, kilos, valor, num in db.execute(
            select(
                Cliente.pais,
                func.coalesce(func.sum(DetalleExportacion.cantidad_kg), 0),
                func.coalesce(func.sum(DetalleExportacion.cantidad_kg * DetalleExportacion.precio_kg), 0),
                func.count(func.distinct(Exportacion.id_exportacion)),
            )
            .select_from(DetalleExportacion)
            .join(Exportacion, Exportacion.id_exportacion == DetalleExportacion.id_exportacion)
            .join(Cliente, Cliente.id_cliente == Exportacion.id_cliente)
            .where(_sin_anuladas())
            .group_by(Cliente.pais)
            .order_by(func.sum(DetalleExportacion.cantidad_kg).desc())
        ).all()
    ]

    # Clientes
    por_cliente = [
        KpiCliente(
            cliente=nombre,
            pais=pais,
            exportaciones=int(num),
            valor=float(round(Decimal(str(valor or 0)), 2)),
        )
        for nombre, pais, num, valor in db.execute(
            select(
                Cliente.nombre_empresa,
                Cliente.pais,
                func.count(func.distinct(Exportacion.id_exportacion)),
                func.coalesce(func.sum(DetalleExportacion.cantidad_kg * DetalleExportacion.precio_kg), 0),
            )
            .select_from(Exportacion)
            .join(Cliente, Cliente.id_cliente == Exportacion.id_cliente)
            .outerjoin(DetalleExportacion, DetalleExportacion.id_exportacion == Exportacion.id_exportacion)
            .where(_sin_anuladas())
            .group_by(Cliente.id_cliente)
            .order_by(func.sum(DetalleExportacion.cantidad_kg * DetalleExportacion.precio_kg).desc())
            .limit(10)
        ).all()
    ]

    # Estado de los contratos
    por_estado = [
        KpiContrato(
            estado=estado,
            count=int(num),
            valor=float(round(Decimal(str(valor or 0)), 2)),
        )
        for estado, num, valor in db.execute(
            select(
                Exportacion.estado,
                func.count(Exportacion.id_exportacion),
                func.coalesce(func.sum(DetalleExportacion.cantidad_kg * DetalleExportacion.precio_kg), 0),
            )
            .select_from(Exportacion)
            .outerjoin(DetalleExportacion, DetalleExportacion.id_exportacion == Exportacion.id_exportacion)
            .group_by(Exportacion.estado)
            .order_by(Exportacion.estado)
        ).all()
    ]

    # Envíos activos y tiempo promedio de entrega
    envios_activos = int(
        db.scalar(
            select(func.count(Envio.id_envio)).where(
                Envio.estado.in_(
                    [
                        EstadoEnvio.PROGRAMADO,
                        EstadoEnvio.EN_TRANSITO,
                        EstadoEnvio.EN_ADUANA,
                        EstadoEnvio.EN_DESTINO,
                        EstadoEnvio.DEMORADO,
                        EstadoEnvio.INCIDENCIA,
                    ]
                )
            )
        )
        or 0
    )

    duraciones = [
        (e.fecha_llegada - e.fecha_salida).days
        for e in db.scalars(
            select(Envio).where(
                Envio.fecha_salida.isnot(None),
                Envio.fecha_llegada.isnot(None),
                Envio.estado == EstadoEnvio.ENTREGADO,
            )
        ).all()
    ]
    tiempo_promedio = round(sum(duraciones) / len(duraciones), 1) if duraciones else None

    clientes_activos = int(
        db.scalar(select(func.count(Cliente.id_cliente)).where(Cliente.activo.is_(True))) or 0
    )

    certificaciones = db.scalars(select(Certificacion)).all()
    por_renovar = sum(
        1
        for c in certificaciones
        if estado_certificacion(c)
        in (EstadoCertificacion.POR_RENOVAR, EstadoCertificacion.VENCIDA)
    )

    lotes_pendientes = int(
        db.scalar(
            select(func.count(Lote.id_lote)).where(
                Lote.estado_calidad.in_(["Pendiente", "En análisis"])
            )
        )
        or 0
    )

    # HU-14 · cartera pendiente consolidada en EUR. Se importa aquí para no
    # crear un ciclo entre indicadores y financiero al cargar el paquete.
    from app.services.financiero import total_pendiente_eur

    return KpiResumen(
        volumen_total_kg=float(volumen_total),
        kilos_cafe=float(kilos_cafe),
        kilos_cacao=float(kilos_cacao),
        ingresos_totales=round(sum(ingresos_por_moneda.values()), 2),
        ingresos_por_moneda=ingresos_por_moneda,
        pedidos=num_pedidos,
        envios_activos=envios_activos,
        clientes_activos=clientes_activos,
        tiempo_promedio_entrega_dias=tiempo_promedio,
        pagos_pendientes=total_pendiente_eur(db),
        por_producto=por_producto,
        por_pais=por_pais,
        por_cliente=por_cliente,
        por_estado=por_estado,
        certificaciones_por_renovar=por_renovar,
        lotes_pendientes_calidad=lotes_pendientes,
    )


# --------------------------------------------------------------------------- #
# Cumplimiento normativo
# --------------------------------------------------------------------------- #
def cumplimiento_normativo(db: Session) -> list[CumplimientoNormativo]:
    """Porcentaje de lotes que cuentan con cada certificación vigente."""
    lotes_total = int(db.scalar(select(func.count(Lote.id_lote))) or 0)
    certificaciones = db.scalars(
        select(Certificacion).where(Certificacion.id_lote.isnot(None))
    ).all()

    hoy = date.today()
    por_tipo: dict[str, list[Certificacion]] = {}
    for cert in certificaciones:
        por_tipo.setdefault(cert.tipo.value, []).append(cert)

    etiquetas = {
        TipoCertificacion.EUDR.value: "EUDR",
        TipoCertificacion.ORGANICO.value: "Orgánico",
        TipoCertificacion.FAIRTRADE.value: "Fairtrade",
    }

    resultado: list[CumplimientoNormativo] = []
    for clave, etiqueta in etiquetas.items():
        items = por_tipo.get(clave, [])
        vigentes = [c for c in items if estado_certificacion(c) in (
            EstadoCertificacion.VIGENTE, EstadoCertificacion.POR_RENOVAR
        )]
        georreferenciados = [c for c in vigentes if c.lote_georreferenciado]
        # Para EUDR solo cuentan los lotes georreferenciados (requisito del Reglamento).
        efectivos = georreferenciados if clave == TipoCertificacion.EUDR.value else vigentes
        porcentaje = round(len(efectivos) / lotes_total * 100) if lotes_total else 0
        proximos = sum(
            1
            for c in items
            if c.fecha_vencimiento
            and 0 <= (c.fecha_vencimiento - hoy).days <= DIAS_RENOVACION
        )
        resultado.append(
            CumplimientoNormativo(
                normativa=etiqueta,
                porcentaje=min(porcentaje, 100),
                detalle=f"{len(efectivos)} de {lotes_total} lotes",
                vencen_pronto=proximos,
            )
        )
    return resultado


# --------------------------------------------------------------------------- #
# Panel general
# --------------------------------------------------------------------------- #
def pedidos_recientes(db: Session, limite: int = 6) -> list[PedidoReciente]:
    """Filas de la tabla «Pedidos recientes» del panel."""
    filas = db.execute(
        select(
            Exportacion,
            Cliente.nombre_empresa,
            Cliente.pais,
            func.coalesce(func.sum(DetalleExportacion.cantidad_kg), 0),
            func.coalesce(func.sum(DetalleExportacion.cantidad_kg * DetalleExportacion.precio_kg), 0),
        )
        .select_from(Exportacion)
        .join(Cliente, Cliente.id_cliente == Exportacion.id_cliente)
        .outerjoin(DetalleExportacion, DetalleExportacion.id_exportacion == Exportacion.id_exportacion)
        .where(_sin_anuladas())
        .group_by(Exportacion.id_exportacion)
        .order_by(Exportacion.fecha.desc(), Exportacion.id_exportacion.desc())
        .limit(limite)
    ).all()

    resultado: list[PedidoReciente] = []
    for exportacion, nombre, pais, kilos, valor in filas:
        producto = db.scalar(
            select(Producto)
            .join(Lote, Lote.id_producto == Producto.id_producto)
            .join(DetalleExportacion, DetalleExportacion.id_lote == Lote.id_lote)
            .where(DetalleExportacion.id_exportacion == exportacion.id_exportacion)
            .limit(1)
        )
        resultado.append(
            PedidoReciente(
                id_exportacion=exportacion.id_exportacion,
                cliente=nombre,
                cliente_pais=pais,
                producto=producto.nombre if producto else "—",
                tipo_producto=producto.tipo if producto else None,
                cantidad_kg=float(Decimal(str(kilos or 0))),
                estado=exportacion.estado,
                valor=float(round(Decimal(str(valor or 0)), 2)),
                moneda=exportacion.moneda,
                puerto_destino=exportacion.puerto_destino,
            )
        )
    return resultado


def ficha_lote(db: Session) -> FichaLote | None:
    """Elemento «Ficha de lote» del panel: el lote más reciente y completo."""
    lote = db.scalars(
        select(Lote)
        .options(
            selectinload(Lote.finca),
            selectinload(Lote.producto),
            selectinload(Lote.certificaciones),
        )
        .order_by(Lote.fecha_cosecha.desc(), Lote.id_lote.desc())
    ).first()
    if lote is None:
        return None

    from app.schemas.catalogos import CertificacionResumida

    certificaciones = [
        CertificacionResumida(
            tipo=c.tipo,
            estado=estado_certificacion(c).value,
            fecha_vencimiento=c.fecha_vencimiento,
        )
        for c in lote.certificaciones
    ]
    return FichaLote(
        id_lote=lote.id_lote,
        codigo_lote=lote.codigo_lote,
        finca=lote.finca.nombre,
        ubicacion=f"{lote.finca.departamento}, Colombia"
        + (f" · {lote.altura_msnm or lote.finca.altura_msnm} msnm"
           if (lote.altura_msnm or lote.finca.altura_msnm)
           else ""),
        altura_msnm=lote.altura_msnm or lote.finca.altura_msnm,
        variedad=lote.variedad or lote.finca.nombre,
        producto=lote.producto.nombre,
        tipo_producto=lote.producto.tipo,
        peso_kg=float(lote.cantidad_kg),
        disponible_kg=float(lote.disponible_kg or lote.cantidad_kg),
        fecha_cosecha=lote.fecha_cosecha,
        estado_calidad=lote.estado_calidad.value,
        certificaciones=certificaciones,
        verificado=bool(certificaciones),
    )


def envio_destacado(db: Session) -> LineaTiempoEnvio | None:
    """Envío en curso para la línea de tiempo del panel."""
    envio = db.scalars(
        select(Envio)
        .options(selectinload(Envio.exportacion).selectinload(Exportacion.cliente))
        .where(Envio.estado.in_([EstadoEnvio.EN_TRANSITO, EstadoEnvio.EN_ADUANA, EstadoEnvio.EN_DESTINO]))
        .order_by(Envio.fecha_llegada.is_(None), Envio.fecha_llegada)
    ).first()
    if envio is None:
        envio = db.scalars(
            select(Envio)
            .options(selectinload(Envio.exportacion).selectinload(Exportacion.cliente))
            .order_by(Envio.id_envio.desc())
        ).first()
    if envio is None:
        return None

    destino = envio.puerto_destino or (
        envio.exportacion.cliente.pais if envio.exportacion and envio.exportacion.cliente else None
    )
    etiqueta = f"Contenedor {envio.numero_seguimiento}"
    if destino:
        etiqueta = f"{etiqueta} · {destino}"
    return LineaTiempoEnvio(
        id_envio=envio.id_envio,
        etiqueta=etiqueta,
        transporte=envio.tipo_transporte,
        numero_seguimiento=envio.numero_seguimiento,
        puerto_origen=envio.puerto_origen,
        puerto_destino=envio.puerto_destino,
        fecha_salida=envio.fecha_salida,
        fecha_llegada=envio.fecha_llegada,
        estado=envio.estado.value,
        etapas=linea_tiempo_envio(envio),
    )


def tarjetas_kpi(db: Session) -> list[ResumenTarjeta]:
    """Las cuatro tarjetas KPI del panel, en el orden del mockup."""
    lotes_activos = int(
        db.scalar(
            select(func.count(Lote.id_lote)).where(Lote.estado_calidad != "Rechazado")
        )
        or 0
    )

    envios_en_curso = int(
        db.scalar(
            select(func.count(Envio.id_envio)).where(
                Envio.estado.in_(
                    [
                        EstadoEnvio.PROGRAMADO,
                        EstadoEnvio.EN_TRANSITO,
                        EstadoEnvio.EN_ADUANA,
                        EstadoEnvio.EN_DESTINO,
                    ]
                )
            )
        )
        or 0
    )
    llegan_semana = int(
        db.scalar(
            select(func.count(Envio.id_envio)).where(
                Envio.fecha_llegada.between(date.today(), date.today() + timedelta(days=7)),
                Envio.estado != EstadoEnvio.ENTREGADO,
            )
        )
        or 0
    )

    certificaciones = db.scalars(select(Certificacion)).all()
    if certificaciones:
        vigentes = sum(
            1
            for c in certificaciones
            if estado_certificacion(c)
            in (EstadoCertificacion.VIGENTE, EstadoCertificacion.POR_RENOVAR)
        )
        pct_cert = round(vigentes / len(certificaciones) * 100)
    else:
        pct_cert = 0
    por_renovar = sum(
        1
        for c in certificaciones
        if estado_certificacion(c)
        in (EstadoCertificacion.POR_RENOVAR, EstadoCertificacion.VENCIDA)
    )

    contratos_abiertos = int(
        db.scalar(
            select(func.count(Exportacion.id_exportacion)).where(
                Exportacion.estado.notin_(
                    [EstadoExportacion.ENTREGADO, EstadoExportacion.ANULADO]
                )
            )
        )
        or 0
    )
    cartera = float(
        db.scalar(
            select(func.coalesce(func.sum(Exportacion.valor_total), 0)).where(
                Exportacion.estado.notin_(
                    [EstadoExportacion.ENTREGADO, EstadoExportacion.ANULADO]
                )
            )
        )
        or 0
    )

    return [
        ResumenTarjeta(
            etiqueta="Lotes activos",
            valor=str(lotes_activos),
            detalle="en inventario para exportación",
            tono="leaf",
        ),
        ResumenTarjeta(
            etiqueta="Contenedores en tránsito",
            valor=str(envios_en_curso),
            detalle=f"{llegan_semana} llegan esta semana",
            tono="eu-blue",
        ),
        ResumenTarjeta(
            etiqueta="Certificaciones vigentes",
            valor=f"{pct_cert}%",
            detalle=f"{por_renovar} por renovar",
            tono="gold",
        ),
        ResumenTarjeta(
            etiqueta="Contratos abiertos",
            valor=str(contratos_abiertos),
            detalle=f"€{round(cartera):,} en cartera",
            tono="rust",
        ),
    ]


def alertas(db: Session) -> list[dict]:
    """Avisos que el panel muestra junto a las notificaciones (HU-16)."""
    hoy = date.today()
    proximo = hoy + timedelta(days=DIAS_RENOVACION)
    resultado: list[dict] = []

    certs = db.scalars(
        select(Certificacion).where(
            Certificacion.fecha_vencimiento.isnot(None),
            Certificacion.fecha_vencimiento <= proximo,
        )
    ).all()
    for cert in certs:
        estado = estado_certificacion(cert)
        if estado in (EstadoCertificacion.VENCIDA, EstadoCertificacion.POR_RENOVAR):
            resultado.append(
                {
                    "tipo": "certificacion",
                    "tono": "rust" if estado == EstadoCertificacion.VENCIDA else "gold",
                    "titulo": f"{cert.tipo.value} · {cert.numero_certificado or 'sin número'}",
                    "detalle": (
                        "Vencida el " + cert.fecha_vencimiento.strftime("%d/%m/%Y")
                        if estado == EstadoCertificacion.VENCIDA
                        else f"Renueva antes del {cert.fecha_vencimiento:%d/%m/%Y}"
                    ),
                }
            )

    envios = db.scalars(
        select(Envio).where(
            Envio.estado.in_([EstadoEnvio.DEMORADO, EstadoEnvio.INCIDENCIA])
        )
    ).all()
    for envio in envios:
        resultado.append(
            {
                "tipo": "envio",
                "tono": "rust",
                "titulo": f"Envío {envio.numero_seguimiento}",
                "detalle": f"{envio.estado.value} · {envio.transportadora}",
            }
        )

    return resultado


def inventario(db: Session) -> ResumenInventario:
    """HU-05 · inventario disponible para exportación."""
    recalcular_disponibles(db)
    total, disponible, lotes = db.execute(
        select(
            func.coalesce(func.sum(Lote.cantidad_kg), 0),
            func.coalesce(func.sum(Lote.disponible_kg), 0),
            func.count(Lote.id_lote),
        )
    ).one()
    comprometido = Decimal(str(total or 0)) - Decimal(str(disponible or 0))

    por_tipo = [
        KpiVolumenProducto(
            tipo=tipo,
            kilos=float(kilos or 0),
            porcentaje=float(
                round(Decimal(str(kilos or 0)) / Decimal(str(disponible or 1)) * 100, 1)
            )
            if disponible
            else 0.0,
        )
        for tipo, kilos in db.execute(
            select(Producto.tipo, func.coalesce(func.sum(Lote.disponible_kg), 0))
            .select_from(Lote)
            .join(Producto, Producto.id_producto == Lote.id_producto)
            .group_by(Producto.tipo)
        ).all()
    ]

    return ResumenInventario(
        kilos_totales=float(Decimal(str(total or 0))),
        kilos_disponibles=float(Decimal(str(disponible or 0))),
        kilos_comprometidos=float(comprometido),
        lotes=int(lotes or 0),
        por_tipo=por_tipo,
    )
