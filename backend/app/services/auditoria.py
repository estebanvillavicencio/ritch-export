"""HU-21 · registro de acciones críticas.

La auditoría se escribe en la misma transacción de la operación que la origina:
si la operación se confirma, el rastro queda; si falla y hay *rollback*, también
desaparece el intento. Las rutas instrumentadas (acceso, contraseña, pagos,
estados, tipos de cambio, integraciones y respaldos) llaman a ``registrar``
directamente; no hay middleware global, así que solo se audita lo que cada
operación decide registrar.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Auditoria, Usuario


def registrar(
    db: Session,
    usuario: Usuario | None,
    accion: str,
    *,
    entidad: str | None = None,
    id_entidad: int | str | None = None,
    detalle: str | None = None,
    metodo: str | None = None,
    ruta: str | None = None,
    estado_http: int | None = None,
    ip: str | None = None,
) -> Auditoria:
    """Añade una fila de auditoría a la sesión (sin hacer *commit*)."""
    fila = Auditoria(
        id_usuario=usuario.id_usuario if usuario is not None else None,
        usuario_correo=usuario.correo if usuario is not None else None,
        accion=accion,
        entidad=entidad,
        id_entidad=str(id_entidad) if id_entidad is not None else None,
        detalle=detalle,
        metodo=metodo,
        ruta=ruta,
        estado_http=estado_http,
        ip=ip,
    )
    db.add(fila)
    return fila

