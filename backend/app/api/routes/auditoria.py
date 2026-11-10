"""Auditoría y seguridad: registro de acciones críticas (HU-21).

Solo el administrador puede consultar el rastro completo. Cada fila indica
quién hizo qué, sobre qué entidad, desde qué ruta e IP y con qué resultado.
"""

from __future__ import annotations

from datetime import date, datetime, time

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.database import get_db
from app.models import Auditoria, Rol, Usuario
from app.schemas import AuditoriaRead, Paginado

router = APIRouter(
    prefix="/auditoria",
    tags=["Auditoría"],
    dependencies=[Depends(get_current_user)],
)

_roles_admin = require_roles(Rol.ADMINISTRADOR)


@router.get("", response_model=Paginado[AuditoriaRead], summary="Listar la auditoría")
def listar_auditoria(
    q: str | None = Query(default=None, description="Busca por acción, correo o entidad"),
    accion: str | None = None,
    entidad: str | None = None,
    id_usuario: int | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    pagina: int = Query(default=1, ge=1),
    tamano: int = Query(default=25, ge=1, le=200),
    db: Session = Depends(get_db),
    _u: Usuario = Depends(_roles_admin),
) -> Paginado[AuditoriaRead]:
    consulta = select(Auditoria)
    if q:
        patron = f"%{q}%"
        consulta = consulta.where(
            or_(
                Auditoria.accion.ilike(patron),
                Auditoria.usuario_correo.ilike(patron),
                Auditoria.entidad.ilike(patron),
                Auditoria.detalle.ilike(patron),
            )
        )
    if accion:
        consulta = consulta.where(Auditoria.accion.ilike(f"%{accion}%"))
    if entidad:
        consulta = consulta.where(Auditoria.entidad == entidad)
    if id_usuario:
        consulta = consulta.where(Auditoria.id_usuario == id_usuario)
    if desde:
        consulta = consulta.where(Auditoria.fecha >= datetime.combine(desde, time.min))
    if hasta:
        consulta = consulta.where(Auditoria.fecha <= datetime.combine(hasta, time.max))

    total = db.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    filas = db.scalars(
        consulta.order_by(Auditoria.fecha.desc(), Auditoria.id_auditoria.desc())
        .offset((pagina - 1) * tamano)
        .limit(tamano)
    ).all()
    return Paginado[AuditoriaRead](
        items=[AuditoriaRead.model_validate(f) for f in filas],
        total=total,
        pagina=pagina,
        tamano=tamano,
    )


@router.get("/{id_auditoria}", response_model=AuditoriaRead, summary="Ver un registro")
def ver_registro(
    id_auditoria: int,
    db: Session = Depends(get_db),
    _u: Usuario = Depends(_roles_admin),
) -> AuditoriaRead:
    fila = db.get(Auditoria, id_auditoria)
    if fila is None:
        raise HTTPException(status_code=404, detail="Registro de auditoría no encontrado")
    return AuditoriaRead.model_validate(fila)
