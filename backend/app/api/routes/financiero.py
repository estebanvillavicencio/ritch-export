"""Módulo financiero: pagos, anticipos, saldos y cartas de crédito (HU-14).

Reglas aplicadas:

* un pago anulado no cuenta para el saldo;
* el total cobrado nunca puede superar el valor del contrato;
* cualquier cambio queda en la auditoría (HU-21) y genera un aviso (HU-16).
"""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, require_roles
from app.database import get_db
from app.models import (
    EstadoPago,
    Exportacion,
    Pago,
    Rol,
    Usuario,
)
from app.schemas import (
    FinancieroResumen,
    Mensaje,
    Paginado,
    PagoCreate,
    PagoRead,
    PagoUpdate,
)
from app.services import auditoria, financiero, monedas, notificaciones

router = APIRouter(tags=["Financiero"], dependencies=[Depends(get_current_user)])

#: El cliente europeo consulta sus pagos, pero no registra ni anula.
_roles_lectura = require_roles(
    Rol.ADMINISTRADOR,
    Rol.FINANCIERO,
    Rol.COMERCIAL,
    Rol.LOGISTICA,
    Rol.CLIENTE_EU,
)
_roles_escritura = require_roles(Rol.ADMINISTRADOR, Rol.FINANCIERO)
_roles_admin = require_roles(Rol.ADMINISTRADOR)


def _a_esquema(pago: Pago) -> PagoRead:
    datos = PagoRead.model_validate(pago)
    if pago.exportacion is not None:
        datos.numero_contrato = pago.exportacion.numero_contrato
        if pago.exportacion.cliente is not None:
            datos.cliente = pago.exportacion.cliente.nombre_empresa
    return datos


def _cargar_pago(db: Session, id_pago: int) -> Pago:
    pago = db.scalar(
        select(Pago)
        .options(
            selectinload(Pago.exportacion).selectinload(Exportacion.cliente),
            selectinload(Pago.usuario),
        )
        .where(Pago.id_pago == id_pago)
    )
    if pago is None:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return pago


def _cargar_exportacion(db: Session, id_exportacion: int) -> Exportacion:
    exportacion = db.scalar(
        select(Exportacion)
        .options(selectinload(Exportacion.cliente))
        .where(Exportacion.id_exportacion == id_exportacion)
    )
    if exportacion is None:
        raise HTTPException(status_code=404, detail="Exportación no encontrada")
    return exportacion


# --------------------------------------------------------------------------- #
# pagos
# --------------------------------------------------------------------------- #
@router.get("/pagos", response_model=Paginado[PagoRead], summary="Listar pagos")
def listar_pagos(
    id_exportacion: int | None = None,
    estado: EstadoPago | None = None,
    moneda: str | None = None,
    q: str | None = Query(default=None, description="Busca por referencia o banco"),
    pagina: int = Query(default=1, ge=1),
    tamano: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(_roles_lectura),
) -> Paginado[PagoRead]:
    consulta = select(Pago).options(
        selectinload(Pago.exportacion).selectinload(Exportacion.cliente),
        selectinload(Pago.usuario),
    )

    # Recorte del portal: el cliente europeo solo ve los pagos de su empresa.
    if usuario.rol == Rol.CLIENTE_EU:
        if usuario.id_cliente is None:
            return Paginado[PagoRead](items=[], total=0, pagina=pagina, tamano=tamano)
        consulta = consulta.join(Exportacion).where(
            Exportacion.id_cliente == usuario.id_cliente
        )
    if id_exportacion:
        consulta = consulta.where(Pago.id_exportacion == id_exportacion)
    if estado:
        consulta = consulta.where(Pago.estado == estado.value)
    if moneda:
        consulta = consulta.where(Pago.moneda == monedas.normalizar(moneda))
    if q:
        patron = f"%{q}%"
        consulta = consulta.where(
            or_(Pago.referencia.ilike(patron), Pago.banco.ilike(patron))
        )

    total = db.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    filas = db.scalars(
        consulta.order_by(Pago.fecha.desc(), Pago.id_pago.desc())
        .offset((pagina - 1) * tamano)
        .limit(tamano)
    ).all()
    return Paginado[PagoRead](
        items=[_a_esquema(p) for p in filas],
        total=total,
        pagina=pagina,
        tamano=tamano,
    )


@router.post(
    "/pagos",
    response_model=PagoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar pago",
)
def crear_pago(
    datos: PagoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(_roles_escritura),
) -> PagoRead:
    """HU-14 · Anticipos, pagos parciales, saldos y cartas de crédito."""
    exportacion = _cargar_exportacion(db, datos.id_exportacion)
    try:
        financiero.validar_pago(db, exportacion, datos.valor, datos.moneda)
    except (ValueError, monedas.ErrorMoneda) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    pago = Pago(
        **datos.model_dump(),
        id_usuario=usuario.id_usuario,
    )
    db.add(pago)
    db.flush()
    notificaciones.notificar_pago(db, pago, exportacion)
    auditoria.registrar(
        db,
        usuario,
        "Registrar pago",
        entidad="pagos",
        id_entidad=pago.id_pago,
        detalle=(
            f"{pago.tipo.value} de {pago.moneda} {float(pago.valor):,.2f} "
            f"para {exportacion.numero_contrato or exportacion.id_exportacion}"
        ),
        metodo="POST",
        ruta="/api/pagos",
        estado_http=201,
    )
    db.commit()
    return _a_esquema(_cargar_pago(db, pago.id_pago))


@router.patch("/pagos/{id_pago}", response_model=PagoRead, summary="Modificar pago")
def actualizar_pago(
    id_pago: int,
    datos: PagoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(_roles_escritura),
) -> PagoRead:
    pago = _cargar_pago(db, id_pago)
    if pago.estado == EstadoPago.ANULADO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un pago anulado no se puede modificar",
        )

    cambios = datos.model_dump(exclude_unset=True)
    valor = cambios.get("valor", pago.valor)
    moneda = cambios.get("moneda", pago.moneda)
    if "valor" in cambios or "moneda" in cambios:
        try:
            financiero.validar_pago(
                db, pago.exportacion, Decimal(str(valor)), moneda, excluir_pago=pago.id_pago
            )
        except (ValueError, monedas.ErrorMoneda) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
            ) from exc

    for campo, nuevo in cambios.items():
        setattr(pago, campo, nuevo)
    auditoria.registrar(
        db,
        usuario,
        "Modificar pago",
        entidad="pagos",
        id_entidad=pago.id_pago,
        detalle="Campos actualizados: " + ", ".join(sorted(cambios)) if cambios else None,
        metodo="PATCH",
        ruta=f"/api/pagos/{id_pago}",
        estado_http=200,
    )
    db.commit()
    return _a_esquema(_cargar_pago(db, id_pago))


@router.post(
    "/pagos/{id_pago}/anular",
    response_model=PagoRead,
    summary="Anular un pago",
)
def anular_pago(
    id_pago: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(_roles_admin),
) -> PagoRead:
    pago = _cargar_pago(db, id_pago)
    if pago.estado == EstadoPago.ANULADO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="El pago ya está anulado"
        )
    pago.estado = EstadoPago.ANULADO
    auditoria.registrar(
        db,
        usuario,
        "Anular pago",
        entidad="pagos",
        id_entidad=pago.id_pago,
        detalle=f"Se anuló {pago.moneda} {float(pago.valor):,.2f}",
        metodo="POST",
        ruta=f"/api/pagos/{id_pago}/anular",
        estado_http=200,
    )
    db.commit()
    return _a_esquema(_cargar_pago(db, id_pago))


@router.delete(
    "/pagos/{id_pago}",
    response_model=Mensaje,
    summary="Eliminar un pago registrado por error",
)
def eliminar_pago(
    id_pago: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(_roles_admin),
) -> Mensaje:
    pago = _cargar_pago(db, id_pago)
    if pago.estado == EstadoPago.CONFIRMADO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un pago confirmado no se elimina: anúlalo para conservar el rastro",
        )
    auditoria.registrar(
        db,
        usuario,
        "Eliminar pago",
        entidad="pagos",
        id_entidad=pago.id_pago,
        detalle=f"Se eliminó {pago.moneda} {float(pago.valor):,.2f}",
        metodo="DELETE",
        ruta=f"/api/pagos/{id_pago}",
        estado_http=200,
    )
    db.delete(pago)
    db.commit()
    return Mensaje(mensaje="Pago eliminado", id=id_pago)


# --------------------------------------------------------------------------- #
# resumen
# --------------------------------------------------------------------------- #
@router.get(
    "/financiero/resumen",
    response_model=FinancieroResumen,
    summary="Resumen financiero consolidado",
)
def resumen_financiero(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(_roles_lectura),
) -> FinancieroResumen:
    """Cartera, cobros y anticipos consolidados en EUR.

    El cliente europeo recibe el mismo formato, pero con su propia cartera:
    la información de los demás importadores no se expone.
    """
    if usuario.rol != Rol.CLIENTE_EU:
        return financiero.resumen(db)

    if usuario.id_cliente is None:
        return FinancieroResumen(
            total_contratado=0.0,
            total_cobrado=0.0,
            total_pendiente=0.0,
            total_anticipos=0.0,
            pagos_confirmados=0,
            pagos_registrados=0,
            pagos_anulados=0,
            contratos_con_saldo=0,
            cartera_vencida=0.0,
        )

    return financiero.resumen(db, id_cliente=usuario.id_cliente)
