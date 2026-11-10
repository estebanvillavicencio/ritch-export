"""HU-14 · pagos, anticipos, saldos y cartas de crédito.

Reglas de negocio:

* un pago anulado no cuenta para el saldo;
* los pagos pueden venir en otra moneda: se convierten a la moneda del contrato
  con el tipo de cambio vigente antes de comparar;
* el total cobrado de un contrato no puede superar su valor;
* el resumen consolidado se expresa en EUR para poder comparar contratos que
  están en monedas distintas.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    EstadoExportacion,
    EstadoPago,
    Exportacion,
    Pago,
    TipoPago,
)
from app.schemas.sprint3 import (
    FinancieroResumen,
    PagoResumenExportacion,
    PagoResumenMoneda,
)
from app.services import monedas

TOLERANCIA = Decimal("0.01")


def pagos_de(db: Session, id_exportacion: int) -> list[Pago]:
    return db.scalars(
        select(Pago)
        .where(Pago.id_exportacion == id_exportacion, Pago.estado != EstadoPago.ANULADO)
        .order_by(Pago.fecha, Pago.id_pago)
    ).all()


def cobrado_exportacion(
    db: Session, exportacion: Exportacion, *, excluir_pago: int | None = None
) -> Decimal:
    """Total cobrado de un contrato, expresado en la moneda del contrato."""
    total = Decimal("0")
    for pago in pagos_de(db, exportacion.id_exportacion):
        if excluir_pago is not None and pago.id_pago == excluir_pago:
            continue
        total += monedas.convertir(db, pago.valor, pago.moneda, exportacion.moneda)
    return total.quantize(Decimal("0.01"))


def validar_pago(
    db: Session,
    exportacion: Exportacion,
    valor: Decimal,
    moneda: str,
    *,
    excluir_pago: int | None = None,
) -> None:
    """Lanza ``ValueError`` si el pago deja el contrato sobrecobrado."""
    if exportacion.estado == EstadoExportacion.ANULADO:
        raise ValueError("No se pueden registrar pagos de una exportación anulada")
    if valor <= 0:
        raise ValueError("El valor del pago debe ser mayor que cero")
    monedas.tasa(db, moneda)  # valida que la moneda exista

    cobrado = cobrado_exportacion(db, exportacion, excluir_pago=excluir_pago)
    nuevo = monedas.convertir(db, valor, moneda, exportacion.moneda)
    if cobrado + nuevo > Decimal(exportacion.valor_total) + TOLERANCIA:
        pendiente = max(Decimal("0"), Decimal(exportacion.valor_total) - cobrado)
        raise ValueError(
            f"El pago supera el saldo del contrato: pendiente "
            f"{exportacion.moneda} {pendiente:,.2f} y se intenta registrar "
            f"{exportacion.moneda} {nuevo:,.2f}"
        )


def resumen(
    db: Session, hoy: date | None = None, *, id_cliente: int | None = None
) -> FinancieroResumen:
    """Indicadores del módulo financiero, consolidados en EUR.

    Con ``id_cliente`` el resumen se recorta a la cartera de ese importador:
    el portal del cliente europeo no ve contratos, pagos ni contadores ajenos.
    """
    hoy = hoy or date.today()
    consulta_exportaciones = (
        select(Exportacion)
        .options(selectinload(Exportacion.cliente))
        .where(Exportacion.estado != EstadoExportacion.ANULADO)
        .order_by(Exportacion.fecha.desc())
    )
    if id_cliente is not None:
        consulta_exportaciones = consulta_exportaciones.where(
            Exportacion.id_cliente == id_cliente
        )
    exportaciones = db.scalars(consulta_exportaciones).all()

    consulta_pagos = select(Pago)
    if id_cliente is not None:
        consulta_pagos = consulta_pagos.join(Exportacion).where(
            Exportacion.id_cliente == id_cliente
        )
    pagos = db.scalars(consulta_pagos).all()
    confirmados = sum(1 for p in pagos if p.estado == EstadoPago.CONFIRMADO)
    registrados = sum(1 for p in pagos if p.estado == EstadoPago.REGISTRADO)
    anulados = sum(1 for p in pagos if p.estado == EstadoPago.ANULADO)

    por_moneda: dict[str, dict[str, Decimal]] = {}
    por_exportacion: list[PagoResumenExportacion] = []
    total_contratado = total_cobrado = total_anticipos = cartera_vencida = Decimal("0")
    contratos_con_saldo = 0

    for exportacion in exportaciones:
        cobrado = cobrado_exportacion(db, exportacion)
        pendiente = max(Decimal("0"), Decimal(exportacion.valor_total) - cobrado)
        porcentaje = (
            round(float(cobrado / Decimal(exportacion.valor_total) * 100), 1)
            if exportacion.valor_total
            else 0.0
        )
        if pendiente > Decimal("0.01"):
            contratos_con_saldo += 1
            if exportacion.fecha <= hoy - timedelta(days=30):
                cartera_vencida += monedas.a_eur(db, pendiente, exportacion.moneda)

        contratado_eur = monedas.a_eur(db, exportacion.valor_total, exportacion.moneda)
        cobrado_eur = monedas.a_eur(db, cobrado, exportacion.moneda)
        total_contratado += contratado_eur
        total_cobrado += cobrado_eur

        grupo = por_moneda.setdefault(
            exportacion.moneda,
            {
                "contratado": Decimal("0"),
                "cobrado": Decimal("0"),
                "pendiente": Decimal("0"),
                "anticipos": Decimal("0"),
            },
        )
        grupo["contratado"] += Decimal(exportacion.valor_total)
        grupo["cobrado"] += cobrado
        grupo["pendiente"] += pendiente

        anticipos = sum(
            (
                monedas.convertir(db, p.valor, p.moneda, exportacion.moneda)
                for p in pagos_de(db, exportacion.id_exportacion)
                if p.tipo == TipoPago.ANTICIPO
            ),
            Decimal("0"),
        )
        grupo["anticipos"] += anticipos
        total_anticipos += monedas.a_eur(db, anticipos, exportacion.moneda)

        por_exportacion.append(
            PagoResumenExportacion(
                id_exportacion=exportacion.id_exportacion,
                numero_contrato=exportacion.numero_contrato,
                cliente=exportacion.cliente.nombre_empresa if exportacion.cliente else "—",
                moneda=exportacion.moneda,
                estado=exportacion.estado.value,
                valor_total=float(exportacion.valor_total),
                cobrado=float(cobrado),
                pendiente=float(pendiente),
                porcentaje=porcentaje,
            )
        )

    return FinancieroResumen(
        total_contratado=round(float(total_contratado), 2),
        total_cobrado=round(float(total_cobrado), 2),
        total_pendiente=round(float(total_contratado - total_cobrado), 2),
        total_anticipos=round(float(total_anticipos), 2),
        pagos_confirmados=confirmados,
        pagos_registrados=registrados,
        pagos_anulados=anulados,
        contratos_con_saldo=contratos_con_saldo,
        cartera_vencida=round(float(cartera_vencida), 2),
        por_moneda=[
            PagoResumenMoneda(
                moneda=moneda,
                contratado=round(float(v["contratado"]), 2),
                cobrado=round(float(v["cobrado"]), 2),
                pendiente=round(float(v["pendiente"]), 2),
                anticipos=round(float(v["anticipos"]), 2),
            )
            for moneda, v in sorted(por_moneda.items())
        ],
        por_exportacion=por_exportacion,
    )


def total_pendiente_eur(db: Session) -> float:
    """Cifra que el panel muestra como «pagos pendientes»."""
    return resumen(db).total_pendiente


def pagos_pendientes_count(db: Session) -> int:
    return int(
        db.scalar(
            select(func.count(Pago.id_pago)).where(Pago.estado == EstadoPago.REGISTRADO)
        )
        or 0
    )
