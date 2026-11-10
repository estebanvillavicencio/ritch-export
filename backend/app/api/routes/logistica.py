"""Módulo de Logística: contenedores, envíos y seguimiento (HU-11, HU-12, HU-13)."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, require_roles
from app.database import get_db
from app.models import (
    Cliente,
    Contenedor,
    Envio,
    EstadoEnvio,
    EstadoExportacion,
    Exportacion,
    Rol,
    Usuario,
)
from app.schemas import (
    ContenedorCreate,
    ContenedorRead,
    ContenedorUpdate,
    EnvioCreate,
    EnvioRead,
    EnvioSeguimiento,
    EnvioUpdate,
    Mensaje,
    Paginado,
)
from app.services.reglas import fecha_llegada_estimada, linea_tiempo_envio

router = APIRouter(tags=["Logística"], dependencies=[Depends(get_current_user)])

_roles_logistica = require_roles(
    Rol.ADMINISTRADOR, Rol.LOGISTICA, Rol.COMERCIAL, Rol.FINANCIERO
)
#: Lectura de envíos y su trazabilidad. El cliente europeo entra, pero las
#: consultas se le recortan a los envíos de su propia empresa.
_roles_seguimiento = require_roles(
    Rol.ADMINISTRADOR, Rol.LOGISTICA, Rol.COMERCIAL, Rol.FINANCIERO, Rol.CLIENTE_EU
)
_roles_admin_logistica = require_roles(Rol.ADMINISTRADOR, Rol.LOGISTICA)


def _es_cliente(usuario: Usuario) -> bool:
    return usuario.rol == Rol.CLIENTE_EU


def _exigir_empresa(usuario: Usuario) -> int:
    """Devuelve el id de cliente de un usuario de portal, o explica por qué no.

    Una cuenta con el rol «Cliente europeo» sin empresa asignada no debe ver
    nada: es preferible un error claro a mostrarle los pedidos de otro.
    """
    if usuario.id_cliente is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Tu cuenta no tiene empresa asignada, así que no hay envíos que "
                "mostrar. Pídele al administrador que la asocie a tu empresa en "
                "la pantalla de usuarios."
            ),
        )
    return usuario.id_cliente


# --------------------------------------------------------------------------- #
# contenedores
# --------------------------------------------------------------------------- #
@router.get("/contenedores", response_model=Paginado[ContenedorRead], summary="Listar contenedores")
def listar_contenedores(
    q: str | None = None,
    solo_disponibles: bool = False,
    pagina: int = Query(default=1, ge=1),
    tamano: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _u: Usuario = Depends(_roles_logistica),
) -> Paginado[ContenedorRead]:
    consulta = select(Contenedor)
    if q:
        patron = f"%{q}%"
        consulta = consulta.where(
            or_(
                Contenedor.codigo.ilike(patron),
                Contenedor.naviera.ilike(patron),
            )
        )
    if solo_disponibles:
        consulta = consulta.where(Contenedor.disponible.is_(True))

    total = db.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    filas = db.scalars(
        consulta.order_by(Contenedor.codigo)
        .offset((pagina - 1) * tamano)
        .limit(tamano)
    ).all()
    return Paginado[ContenedorRead](
        items=[ContenedorRead.model_validate(c) for c in filas],
        total=total,
        pagina=pagina,
        tamano=tamano,
    )


@router.post(
    "/contenedores",
    response_model=ContenedorRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar contenedor",
)
def crear_contenedor(
    datos: ContenedorCreate,
    db: Session = Depends(get_db),
    _u: Usuario = Depends(_roles_admin_logistica),
) -> ContenedorRead:
    if db.scalar(select(Contenedor).where(Contenedor.codigo == datos.codigo)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un contenedor con el código {datos.codigo}",
        )
    contenedor = Contenedor(**datos.model_dump())
    db.add(contenedor)
    db.commit()
    db.refresh(contenedor)
    return ContenedorRead.model_validate(contenedor)


@router.patch(
    "/contenedores/{id_contenedor}",
    response_model=ContenedorRead,
    summary="Modificar contenedor",
)
def actualizar_contenedor(
    id_contenedor: int,
    datos: ContenedorUpdate,
    db: Session = Depends(get_db),
    _u: Usuario = Depends(_roles_admin_logistica),
) -> ContenedorRead:
    contenedor = db.get(Contenedor, id_contenedor)
    if contenedor is None:
        raise HTTPException(status_code=404, detail="Contenedor no encontrado")
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(contenedor, campo, valor)
    db.commit()
    db.refresh(contenedor)
    return ContenedorRead.model_validate(contenedor)


# --------------------------------------------------------------------------- #
# envíos · HU-12
# --------------------------------------------------------------------------- #
@router.get("/envios", response_model=Paginado[EnvioSeguimiento], summary="Listar envíos")
def listar_envios(
    id_exportacion: int | None = None,
    estado: EstadoEnvio | None = None,
    q: str | None = Query(default=None, description="Busca por número de seguimiento"),
    pagina: int = Query(default=1, ge=1),
    tamano: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    u: Usuario = Depends(_roles_seguimiento),
) -> Paginado[EnvioSeguimiento]:
    consulta = (
        select(Envio)
        .options(
            selectinload(Envio.exportacion).selectinload(Exportacion.cliente),
            selectinload(Envio.contenedor),
        )
        .join(Envio.exportacion)
    )
    # HU-10 · El cliente ve solo los envíos de su empresa. El recorte va primero
    # para que ningún filtro de la URL pueda ampliarlo.
    if _es_cliente(u):
        consulta = consulta.where(Exportacion.id_cliente == _exigir_empresa(u))
    if id_exportacion:
        consulta = consulta.where(Envio.id_exportacion == id_exportacion)
    if estado:
        consulta = consulta.where(Envio.estado == estado.value)
    if q:
        consulta = consulta.where(
            or_(
                Envio.numero_seguimiento.ilike(f"%{q}%"),
                Envio.transportadora.ilike(f"%{q}%"),
            )
        )

    total = db.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    filas = db.scalars(
        consulta.order_by(Envio.id_envio.desc()).offset((pagina - 1) * tamano).limit(tamano)
    ).all()
    return Paginado[EnvioSeguimiento](
        items=[_a_seguimiento(e) for e in filas],
        total=total,
        pagina=pagina,
        tamano=tamano,
    )


def _a_seguimiento(envio: Envio) -> EnvioSeguimiento:
    """ Enriquece el envío con cliente, días de tránsito y etapa actual. """
    hoy = date.today()
    dias = None
    restantes = None
    if envio.fecha_salida and envio.fecha_llegada:
        dias = (envio.fecha_llegada - envio.fecha_salida).days
    if envio.fecha_llegada and envio.fecha_llegada >= hoy:
        restantes = (envio.fecha_llegada - hoy).days

    etapas = linea_tiempo_envio(envio)
    actual = next((e["etapa"] for e in etapas if e["estado"] == "current"), None)

    cliente = envio.exportacion.cliente if envio.exportacion else None
    return EnvioSeguimiento(
        **EnvioRead.model_validate(envio).model_dump(),
        cliente_nombre=cliente.nombre_empresa if cliente else None,
        cliente_pais=cliente.pais if cliente else None,
        dias_transito=dias,
        dias_restantes=restantes,
        etapa_actual=actual,
    )


@router.post(
    "/envios",
    response_model=EnvioRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar envío",
)
def crear_envio(
    datos: EnvioCreate,
    db: Session = Depends(get_db),
    _u: Usuario = Depends(_roles_admin_logistica),
) -> EnvioRead:
    """HU-12 · Coordinar transporte, contenedores y rutas.

    Al crear el envío, si la exportación ya está en puerto o tránsito, la
    operación avanza a «En tránsito» de forma coherente con el seguimiento.
    """
    exportacion = db.get(Exportacion, datos.id_exportacion)
    if exportacion is None:
        raise HTTPException(status_code=404, detail="Exportación no encontrada")

    if db.scalar(
        select(Envio).where(Envio.numero_seguimiento == datos.numero_seguimiento)
    ) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El número de seguimiento {datos.numero_seguimiento} ya existe",
        )

    if datos.id_contenedor:
        contenedor = db.get(Contenedor, datos.id_contenedor)
        if contenedor is None:
            raise HTTPException(status_code=404, detail="El contenedor indicado no existe")
        peso = exportacion.total_kg
        if peso > contenedor.capacidad_kg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"La exportación pesa {peso} kg y el contenedor {contenedor.codigo} "
                    f"soporta {contenedor.capacidad_kg} kg"
                ),
            )
        contenedor.disponible = False

    envio = Envio(**datos.model_dump())
    db.add(envio)

    # Sincroniza el estado de la exportación con el del envío.
    if envio.estado in (EstadoEnvio.EN_TRANSITO, EstadoEnvio.EN_ADUANA):
        if exportacion.estado in (
            EstadoExportacion.PEDIDO_RECIBIDO,
            EstadoExportacion.EN_PREPARACION,
            EstadoExportacion.EN_PRODUCCION,
        ):
            exportacion.estado = EstadoExportacion.EN_PUERTO
    elif envio.estado == EstadoEnvio.ENTREGADO and exportacion.estado != EstadoExportacion.ENTREGADO:
        exportacion.estado = EstadoExportacion.ENTREGADO

    db.commit()
    db.refresh(envio)
    return EnvioRead.model_validate(envio)


def _cargar_envio(db: Session, id_envio: int, usuario: Usuario | None = None) -> Envio:
    """Carga un envío y, si quien pregunta es un cliente, se cernea.

    Un 404 y no un 403 cuando el envío es de otra empresa: así tampoco se le
    confirma que ese número de seguimiento existe.
    """
    envio = db.scalar(
        select(Envio)
        .options(
            selectinload(Envio.exportacion).selectinload(Exportacion.cliente),
            selectinload(Envio.contenedor),
        )
        .where(Envio.id_envio == id_envio)
    )
    if envio is None:
        raise HTTPException(status_code=404, detail="Envío no encontrado")
    if usuario is not None and _es_cliente(usuario):
        if envio.exportacion.id_cliente != _exigir_empresa(usuario):
            raise HTTPException(status_code=404, detail="Envío no encontrado")
    return envio


@router.get("/envios/{id_envio}", response_model=EnvioSeguimiento, summary="Ver envío")
def obtener_envio(
    id_envio: int,
    db: Session = Depends(get_db),
    u: Usuario = Depends(_roles_seguimiento),
) -> EnvioSeguimiento:
    return _a_seguimiento(_cargar_envio(db, id_envio, u))


@router.get(
    "/envios/{id_envio}/trazabilidad", response_model=list[dict], summary="Línea de tiempo del envío"
)
def trazabilidad_envio(
    id_envio: int,
    db: Session = Depends(get_db),
    u: Usuario = Depends(_roles_seguimiento),
) -> list[dict]:
    """Las seis etapas del envío, tal como se muestran en el panel general."""
    return linea_tiempo_envio(_cargar_envio(db, id_envio, u))


@router.patch("/envios/{id_envio}", response_model=EnvioSeguimiento, summary="Actualizar envío")
def actualizar_envio(
    id_envio: int,
    datos: EnvioUpdate,
    db: Session = Depends(get_db),
    _u: Usuario = Depends(_roles_admin_logistica),
) -> EnvioSeguimiento:
    """Informe §6.9 · Actualizar el estado del envío y su trazabilidad."""
    envio = db.get(Envio, id_envio)
    if envio is None:
        raise HTTPException(status_code=404, detail="Envío no encontrado")

    cambios = datos.model_dump(exclude_unset=True)
    for campo, valor in cambios.items():
        setattr(envio, campo, valor)

    exportacion = db.get(Exportacion, envio.id_exportacion)
    if exportacion is not None:
        if envio.estado == EstadoEnvio.ENTREGADO and envio.fecha_llegada:
            exportacion.estado = EstadoExportacion.ENTREGADO
        elif envio.estado in (EstadoEnvio.EN_ADUANA, EstadoEnvio.EN_DESTINO):
            exportacion.estado = EstadoExportacion.EN_DESTINO
        elif envio.estado == EstadoEnvio.EN_TRANSITO and exportacion.estado in (
            EstadoExportacion.PEDIDO_RECIBIDO,
            EstadoExportacion.EN_PREPARACION,
            EstadoExportacion.EN_PRODUCCION,
        ):
            exportacion.estado = EstadoExportacion.EN_PUERTO

    db.commit()
    db.refresh(envio)
    return _a_seguimiento(
        db.scalar(
            select(Envio)
            .options(
                selectinload(Envio.exportacion).selectinload(Exportacion.cliente),
                selectinload(Envio.contenedor),
            )
            .where(Envio.id_envio == id_envio)
        )
    )


@router.delete("/envios/{id_envio}", response_model=Mensaje, summary="Anular envío")
def anular_envio(
    id_envio: int,
    db: Session = Depends(get_db),
    _u: Usuario = Depends(_roles_admin_logistica),
) -> Mensaje:
    """Los envíos no se borran: quedan como «Incidencia» para conservar la
    trazabilidad del envío que no llegó a destino."""
    envio = db.get(Envio, id_envio)
    if envio is None:
        raise HTTPException(status_code=404, detail="Envío no encontrado")
    if envio.estado == EstadoEnvio.ENTREGADO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un envío entregado no puede anularse",
        )
    if envio.contenedor_id or envio.contenedor:
        envio.contenedor.disponible = True
    envio.estado = EstadoEnvio.INCIDENCIA
    db.commit()
    return Mensaje(mensaje=f"Envío {envio.numero_seguimiento} marcado con incidencia", id=id_envio)
