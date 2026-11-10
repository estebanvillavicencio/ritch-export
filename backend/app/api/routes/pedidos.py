"""Solicitudes de pedido iniciadas por compradores europeos."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.database import get_db
from app.models import Cliente, Producto, Rol, SolicitudPedido, Usuario
from app.schemas.pedidos import SolicitudPedidoCreate, SolicitudPedidoRead

router = APIRouter(tags=["Solicitudes de pedido"], dependencies=[Depends(get_current_user)])


def _salida(fila: SolicitudPedido) -> SolicitudPedidoRead:
    return SolicitudPedidoRead(
        id_solicitud=fila.id_solicitud,
        id_cliente=fila.id_cliente,
        id_usuario=fila.id_usuario,
        id_producto=fila.id_producto,
        cantidad_kg=fila.cantidad_kg,
        incoterm=fila.incoterm,
        puerto_destino=fila.puerto_destino,
        observaciones=fila.observaciones,
        estado=fila.estado,
        created_at=fila.created_at,
        producto_nombre=fila.producto.nombre,
        empresa=fila.cliente.nombre_empresa,
    )


@router.post("/solicitudes-pedido", response_model=SolicitudPedidoRead,
             status_code=status.HTTP_201_CREATED)
def crear_solicitud(
    datos: SolicitudPedidoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> SolicitudPedidoRead:
    if usuario.rol != Rol.CLIENTE_EU:
        raise HTTPException(status_code=403, detail="Solo un comprador puede enviar una solicitud desde el portal")
    if usuario.id_cliente is None:
        raise HTTPException(status_code=403, detail="La cuenta no tiene una empresa compradora asociada")
    producto = db.get(Producto, datos.id_producto)
    if producto is None or not producto.activo:
        raise HTTPException(status_code=404, detail="El producto no está disponible")
    cliente = db.get(Cliente, usuario.id_cliente)
    if cliente is None:
        raise HTTPException(status_code=403, detail="La empresa asociada a la cuenta no existe")
    solicitud = SolicitudPedido(
        id_cliente=cliente.id_cliente,
        id_usuario=usuario.id_usuario,
        id_producto=producto.id_producto,
        cantidad_kg=datos.cantidad_kg,
        incoterm=datos.incoterm,
        puerto_destino=datos.puerto_destino or cliente.puerto_destino,
        observaciones=datos.observaciones,
        estado="Pendiente",
    )
    db.add(solicitud)
    db.commit()
    db.refresh(solicitud)
    solicitud.producto = producto
    solicitud.cliente = cliente
    return _salida(solicitud)


@router.get("/solicitudes-pedido", response_model=list[SolicitudPedidoRead])
def listar_solicitudes(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> list[SolicitudPedidoRead]:
    consulta = select(SolicitudPedido).options(
        joinedload(SolicitudPedido.producto), joinedload(SolicitudPedido.cliente)
    )
    if usuario.rol == Rol.CLIENTE_EU:
        if usuario.id_cliente is None:
            return []
        consulta = consulta.where(SolicitudPedido.id_cliente == usuario.id_cliente)
    elif usuario.rol not in (Rol.ADMINISTRADOR, Rol.COMERCIAL):
        raise HTTPException(status_code=403, detail="No tienes permiso para consultar solicitudes")
    filas = db.scalars(consulta.order_by(SolicitudPedido.created_at.desc())).all()
    return [_salida(fila) for fila in filas]
