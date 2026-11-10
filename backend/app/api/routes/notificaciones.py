"""Bandeja de notificaciones y avisos del sistema (HU-16).

El listado sincroniza primero las alertas derivadas (certificaciones, envíos,
saldos) para que la bandeja no dependa de una tarea programada externa.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.database import get_db
from app.models import Rol, Usuario
from app.schemas import (
    ContadorNotificaciones,
    Mensaje,
    NotificacionCreate,
    NotificacionRead,
)
from app.services import notificaciones

router = APIRouter(
    prefix="/notificaciones",
    tags=["Notificaciones"],
    dependencies=[Depends(get_current_user)],
)

_roles_admin = require_roles(Rol.ADMINISTRADOR)


@router.get("", response_model=list[NotificacionRead], summary="Listar notificaciones")
def listar_notificaciones(
    solo_no_leidas: bool = False,
    limite: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> list[NotificacionRead]:
    notificaciones.sincronizar_alertas(db)
    db.commit()
    return [
        NotificacionRead.model_validate(a)
        for a in notificaciones.listar(db, usuario, solo_no_leidas=solo_no_leidas, limite=limite)
    ]


@router.get(
    "/contador",
    response_model=ContadorNotificaciones,
    summary="Contar notificaciones de la bandeja",
)
def contador(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> ContadorNotificaciones:
    total, no_leidas = notificaciones.contar(db, usuario)
    return ContadorNotificaciones(total=total, no_leidas=no_leidas)


@router.post(
    "/{id_notificacion}/leer",
    response_model=NotificacionRead,
    summary="Marcar una notificación como leída",
)
def marcar_leida(
    id_notificacion: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> NotificacionRead:
    try:
        aviso = notificaciones.marcar(db, usuario, id_notificacion)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    db.commit()
    db.refresh(aviso)
    return NotificacionRead.model_validate(aviso)


@router.post("/leer-todas", response_model=Mensaje, summary="Marcar todas como leídas")
def marcar_todas(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> Mensaje:
    cantidad = notificaciones.marcar_todas(db, usuario)
    db.commit()
    return Mensaje(mensaje=f"{cantidad} notificación(es) marcadas como leídas", id=cantidad)


@router.post(
    "",
    response_model=NotificacionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una notificación (administrador)",
)
def crear_notificacion(
    datos: NotificacionCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(_roles_admin),
) -> NotificacionRead:
    aviso = notificaciones.crear(
        db,
        titulo=datos.titulo,
        detalle=datos.detalle,
        tipo=datos.tipo,
        tono=datos.tono,
        enlace=datos.enlace,
        id_usuario=datos.id_usuario,
        rol_destino=datos.rol_destino,
        clave=datos.clave,
    )
    db.commit()
    db.refresh(aviso)
    return NotificacionRead.model_validate(aviso)
