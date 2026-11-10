"""HU-16 · notificaciones y alertas.

Los avisos se generan por dos vías:

* **Derivados** — certificaciones próximas a vencer, envíos con incidencia y
  contratos con saldo pendiente. `sincronizar_alertas()` los crea de forma
  idempotente usando la columna `clave`: dos ejecuciones del mismo hecho dejan
  una sola notificación.
* **Directos** — al registrar un pago o cambiar el estado de un pedido, la ruta
  crea el aviso en la misma transacción.

La bandeja se recorta por destinatario: una cuenta ve las notificaciones
dirigidas a ella, las de su rol y las globales (sin usuario ni rol).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.models import (
    Certificacion,
    Envio,
    EstadoCertificacion,
    EstadoEnvio,
    EstadoPago,
    EstadoExportacion,
    Exportacion,
    Notificacion,
    Pago,
    Rol,
    TipoNotificacion,
    Usuario,
)
from app.services.reglas import DIAS_RENOVACION, estado_certificacion


def crear(
    db: Session,
    *,
    titulo: str,
    detalle: str | None = None,
    tipo: TipoNotificacion = TipoNotificacion.SISTEMA,
    tono: str = "azul",
    enlace: str | None = None,
    id_usuario: int | None = None,
    rol_destino: str | None = None,
    clave: str | None = None,
) -> Notificacion | None:
    """Crea una notificación. Con `clave`, no duplica una ya existente."""
    if clave:
        existente = db.scalar(select(Notificacion).where(Notificacion.clave == clave))
        if existente is not None:
            return existente
    aviso = Notificacion(
        titulo=titulo,
        detalle=detalle,
        tipo=tipo,
        tono=tono,
        enlace=enlace,
        id_usuario=id_usuario,
        rol_destino=rol_destino,
        clave=clave,
    )
    db.add(aviso)
    return aviso


def _destinatarios(db: Session) -> list[Usuario]:
    return db.scalars(select(Usuario).where(Usuario.estado == "activo")).all()


def sincronizar_alertas(db: Session, hoy: date | None = None) -> int:
    """Crea los avisos derivados que falten. Devuelve cuántos creó."""
    hoy = hoy or date.today()
    antes = db.scalar(select(func.count(Notificacion.id_notificacion))) or 0

    # 1. Certificaciones vencidas o por renovar
    limite = hoy + timedelta(days=DIAS_RENOVACION)
    certificaciones = db.scalars(
        select(Certificacion).where(
            Certificacion.fecha_vencimiento.isnot(None),
            Certificacion.fecha_vencimiento <= limite,
        )
    ).all()
    for cert in certificaciones:
        estado = estado_certificacion(cert, hoy)
        if estado not in (EstadoCertificacion.VENCIDA, EstadoCertificacion.POR_RENOVAR):
            continue
        vencida = estado == EstadoCertificacion.VENCIDA
        crear(
            db,
            titulo=f"{cert.tipo.value} · {cert.numero_certificado or 'sin número'}",
            detalle=(
                "La certificación venció el "
                + cert.fecha_vencimiento.strftime("%d/%m/%Y")
                if vencida
                else f"Renueva antes del {cert.fecha_vencimiento:%d/%m/%Y}"
            ),
            tipo=TipoNotificacion.CERTIFICACION,
            tono="rust" if vencida else "gold",
            enlace="#/lotes",
            clave=f"cert-{cert.id_certificacion}-{estado.value}",
        )

    # 2. Envíos demorados o con incidencia
    envios = db.scalars(
        select(Envio).where(Envio.estado.in_([EstadoEnvio.DEMORADO, EstadoEnvio.INCIDENCIA]))
    ).all()
    for envio in envios:
        crear(
            db,
            titulo=f"Envío {envio.numero_seguimiento} · {envio.estado.value}",
            detalle=f"{envio.transportadora} · {envio.puerto_origen or 'origen'} → "
            f"{envio.puerto_destino or 'destino'}",
            tipo=TipoNotificacion.ENVIO,
            tono="rust",
            enlace="#/logistica",
            clave=f"envio-{envio.id_envio}-{envio.estado.value}",
        )

    # 3. Contratos con saldo pendiente (después del Sprint 3)
    pagos = dict(
        db.execute(
            select(Pago.id_exportacion, func.coalesce(func.sum(Pago.valor), 0))
            .where(Pago.estado != EstadoPago.ANULADO)
            .group_by(Pago.id_exportacion)
        ).all()
    )
    exportaciones = db.scalars(
        select(Exportacion).where(
            Exportacion.estado.notin_([EstadoExportacion.ANULADO, EstadoExportacion.ENTREGADO])
        )
    ).all()
    for exportacion in exportaciones:
        cobrado = Decimal(str(pagos.get(exportacion.id_exportacion, 0)))
        if exportacion.valor_total and cobrado < exportacion.valor_total:
            porcentaje = round(float(cobrado / exportacion.valor_total * 100))
            crear(
                db,
                titulo=f"Saldo pendiente · {exportacion.numero_contrato or exportacion.id_exportacion}",
                detalle=f"{porcentaje}% cobrado de {exportacion.moneda} "
                f"{float(exportacion.valor_total):,.0f}",
                tipo=TipoNotificacion.PAGO,
                tono="gold",
                enlace="#/financiero",
                rol_destino=Rol.FINANCIERO.value,
                clave=f"saldo-{exportacion.id_exportacion}-{porcentaje}",
            )

    db.flush()
    despues = db.scalar(select(func.count(Notificacion.id_notificacion))) or 0
    return int(despues - antes)


def consulta_para(usuario: Usuario):
    """Condición SQL de la bandeja visible para un usuario."""
    if usuario.rol == Rol.CLIENTE_EU:
        return Notificacion.id_usuario == usuario.id_usuario
    return or_(
        Notificacion.id_usuario == usuario.id_usuario,
        and_(
            Notificacion.id_usuario.is_(None),
            or_(
                Notificacion.rol_destino.is_(None),
                Notificacion.rol_destino == usuario.rol.value,
            ),
        ),
    )


def listar(
    db: Session,
    usuario: Usuario,
    *,
    solo_no_leidas: bool = False,
    limite: int = 50,
) -> list[Notificacion]:
    consulta = select(Notificacion).where(consulta_para(usuario))
    if solo_no_leidas:
        consulta = consulta.where(Notificacion.leida.is_(False))
    return db.scalars(
        consulta.order_by(Notificacion.fecha.desc(), Notificacion.id_notificacion.desc()).limit(
            limite
        )
    ).all()


def contar(db: Session, usuario: Usuario) -> tuple[int, int]:
    total = db.scalar(
        select(func.count(Notificacion.id_notificacion)).where(consulta_para(usuario))
    ) or 0
    no_leidas = db.scalar(
        select(func.count(Notificacion.id_notificacion)).where(
            consulta_para(usuario), Notificacion.leida.is_(False)
        )
    ) or 0
    return int(total), int(no_leidas)


def marcar(db: Session, usuario: Usuario, id_notificacion: int, leida: bool = True) -> Notificacion:
    aviso = db.scalar(
        select(Notificacion).where(
            Notificacion.id_notificacion == id_notificacion,
            consulta_para(usuario),
        )
    )
    if aviso is None:
        raise ValueError("La notificación no existe o no está dirigida a tu cuenta")
    aviso.leida = leida
    return aviso


def marcar_todas(db: Session, usuario: Usuario) -> int:
    avisos = db.scalars(
        select(Notificacion).where(consulta_para(usuario), Notificacion.leida.is_(False))
    ).all()
    for aviso in avisos:
        aviso.leida = True
    return len(avisos)


def notificar_pago(db: Session, pago: Pago, exportacion: Exportacion) -> None:
    crear(
        db,
        titulo=f"Pago {pago.tipo.value} registrado",
        detalle=f"{exportacion.numero_contrato or exportacion.id_exportacion} · "
        f"{pago.moneda} {float(pago.valor):,.2f} · {pago.metodo.value}",
        tipo=TipoNotificacion.PAGO,
        tono="verde",
        enlace="#/financiero",
        rol_destino=Rol.FINANCIERO.value,
        clave=None,
    )


def notificar_cambio_estado(
    db: Session, exportacion: Exportacion, anterior: str, nuevo: str, usuario: Usuario | None
) -> None:
    crear(
        db,
        titulo=f"Pedido {exportacion.numero_contrato or exportacion.id_exportacion}: {nuevo}",
        detalle=f"Cambió de «{anterior}» a «{nuevo}»"
        + (f" por {usuario.nombre}" if usuario else ""),
        tipo=TipoNotificacion.PEDIDO,
        tono="azul",
        enlace="#/comercial",
        rol_destino=Rol.COMERCIAL.value,
    )


def ahora() -> datetime:
    return datetime.now()
