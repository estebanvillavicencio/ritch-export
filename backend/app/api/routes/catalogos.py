"""Catálogos base: clientes de la UE, productos y fincas.

Módulo Comercial (clientes, productos) y módulo de Productores (fincas).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.database import get_db
from app.models import (
    Cliente,
    Finca,
    PaisUE,
    Producto,
    PuertoOrigen,
    PuertoUE,
    Rol,
    Usuario,
)
from app.schemas import (
    ClienteCreate,
    ClienteRead,
    ClienteResumen,
    ClienteUpdate,
    FincaCreate,
    FincaRead,
    FincaUpdate,
    Mensaje,
    Paginado,
    ProductoCreate,
    ProductoRead,
    ProductoUpdate,
)

router = APIRouter(tags=["Catálogos"], dependencies=[Depends(get_current_user)])

#: Roles que pueden consultar el catálogo; el cliente europeo tiene acceso de
#: solo lectura a productos (portal, Informe §8).
_roles_comercial = require_roles(
    Rol.ADMINISTRADOR, Rol.COMERCIAL, Rol.LOGISTICA, Rol.CALIDAD, Rol.FINANCIERO
)
_roles_lectura = require_roles(
    Rol.ADMINISTRADOR,
    Rol.COMERCIAL,
    Rol.LOGISTICA,
    Rol.CALIDAD,
    Rol.FINANCIERO,
    Rol.CLIENTE_EU,
)


# --------------------------------------------------------------------------- #
# clientes · HU-03
# --------------------------------------------------------------------------- #
@router.get("/clientes", response_model=Paginado[ClienteRead], summary="Listar clientes")
def listar_clientes(
    q: str | None = Query(default=None, description="Busca por empresa o país"),
    pais: str | None = None,
    solo_activos: bool = True,
    pagina: int = Query(default=1, ge=1),
    tamano: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _u: Usuario = Depends(_roles_comercial),
) -> Paginado[ClienteRead]:
    consulta = select(Cliente)
    if q:
        patron = f"%{q}%"
        consulta = consulta.where(
            or_(
                Cliente.nombre_empresa.ilike(patron),
                Cliente.pais.ilike(patron),
                Cliente.vat.ilike(patron),
            )
        )
    if pais:
        consulta = consulta.where(Cliente.pais == pais)
    if solo_activos:
        consulta = consulta.where(Cliente.activo.is_(True))

    total = db.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    filas = db.scalars(
        consulta.order_by(Cliente.nombre_empresa)
        .offset((pagina - 1) * tamano)
        .limit(tamano)
    ).all()
    return Paginado[ClienteRead](
        items=[ClienteRead.model_validate(c) for c in filas],
        total=total,
        pagina=pagina,
        tamano=tamano,
    )


@router.post(
    "/clientes",
    response_model=ClienteRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar cliente importador europeo",
)
def crear_cliente(
    datos: ClienteCreate,
    db: Session = Depends(get_db),
    _u: Usuario = Depends(require_roles(Rol.ADMINISTRADOR, Rol.COMERCIAL)),
) -> ClienteRead:
    cliente = Cliente(**datos.model_dump())
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return ClienteRead.model_validate(cliente)


@router.get("/clientes/{id_cliente}", response_model=ClienteRead, summary="Ver cliente")
def obtener_cliente(
    id_cliente: int,
    db: Session = Depends(get_db),
    _u: Usuario = Depends(_roles_comercial),
) -> ClienteRead:
    cliente = db.get(Cliente, id_cliente)
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return ClienteRead.model_validate(cliente)


@router.patch("/clientes/{id_cliente}", response_model=ClienteRead, summary="Modificar cliente")
def actualizar_cliente(
    id_cliente: int,
    datos: ClienteUpdate,
    db: Session = Depends(get_db),
    _u: Usuario = Depends(require_roles(Rol.ADMINISTRADOR, Rol.COMERCIAL)),
) -> ClienteRead:
    cliente = db.get(Cliente, id_cliente)
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(cliente, campo, valor)
    db.commit()
    db.refresh(cliente)
    return ClienteRead.model_validate(cliente)


# --------------------------------------------------------------------------- #
# productos
# --------------------------------------------------------------------------- #
@router.get("/productos", response_model=Paginado[ProductoRead], summary="Listar productos")
def listar_productos(
    q: str | None = None,
    tipo: str | None = Query(default=None, description="Café | Cacao"),
    pagina: int = Query(default=1, ge=1),
    tamano: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _u: Usuario = Depends(_roles_lectura),
) -> Paginado[ProductoRead]:
    consulta = select(Producto)
    if q:
        consulta = consulta.where(Producto.nombre.ilike(f"%{q}%"))
    if tipo:
        consulta = consulta.where(Producto.tipo == tipo)

    total = db.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    filas = db.scalars(
        consulta.order_by(Producto.tipo, Producto.nombre)
        .offset((pagina - 1) * tamano)
        .limit(tamano)
    ).all()
    return Paginado[ProductoRead](
        items=[ProductoRead.model_validate(p) for p in filas],
        total=total,
        pagina=pagina,
        tamano=tamano,
    )


@router.post(
    "/productos",
    response_model=ProductoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar producto",
)
def crear_producto(
    datos: ProductoCreate,
    db: Session = Depends(get_db),
    _u: Usuario = Depends(require_roles(Rol.ADMINISTRADOR, Rol.COMERCIAL, Rol.CALIDAD)),
) -> ProductoRead:
    producto = Producto(**datos.model_dump())
    db.add(producto)
    db.commit()
    db.refresh(producto)
    return ProductoRead.model_validate(producto)


@router.patch(
    "/productos/{id_producto}", response_model=ProductoRead, summary="Modificar producto"
)
def actualizar_producto(
    id_producto: int,
    datos: ProductoUpdate,
    db: Session = Depends(get_db),
    _u: Usuario = Depends(require_roles(Rol.ADMINISTRADOR, Rol.COMERCIAL, Rol.CALIDAD)),
) -> ProductoRead:
    producto = db.get(Producto, id_producto)
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(producto, campo, valor)
    db.commit()
    db.refresh(producto)
    return ProductoRead.model_validate(producto)


# --------------------------------------------------------------------------- #
# fincas · HU-04
# --------------------------------------------------------------------------- #
@router.get("/fincas", response_model=Paginado[FincaRead], summary="Listar fincas")
def listar_fincas(
    q: str | None = Query(default=None, description="Busca por nombre, propietario o asociación"),
    departamento: str | None = None,
    pagina: int = Query(default=1, ge=1),
    tamano: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _u: Usuario = Depends(_roles_comercial),
) -> Paginado[FincaRead]:
    consulta = select(Finca)
    if q:
        patron = f"%{q}%"
        consulta = consulta.where(
            or_(
                Finca.nombre.ilike(patron),
                Finca.propietario.ilike(patron),
                Finca.asociacion.ilike(patron),
                Finca.ubicacion.ilike(patron),
            )
        )
    if departamento:
        consulta = consulta.where(Finca.departamento == departamento)

    total = db.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    filas = db.scalars(
        consulta.order_by(Finca.nombre)
        .offset((pagina - 1) * tamano)
        .limit(tamano)
    ).all()
    return Paginado[FincaRead](
        items=[FincaRead.model_validate(f) for f in filas],
        total=total,
        pagina=pagina,
        tamano=tamano,
    )


@router.post(
    "/fincas",
    response_model=FincaRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar finca o asociación",
)
def crear_finca(
    datos: FincaCreate,
    db: Session = Depends(get_db),
    _u: Usuario = Depends(require_roles(Rol.ADMINISTRADOR, Rol.COMERCIAL, Rol.CALIDAD)),
) -> FincaRead:
    """HU-04 · Registrar fincas y asociaciones de café y cacao."""
    finca = Finca(**datos.model_dump())
    db.add(finca)
    db.commit()
    db.refresh(finca)
    return FincaRead.model_validate(finca)


@router.get("/fincas/{id_finca}", response_model=FincaRead, summary="Ver finca")
def obtener_finca(
    id_finca: int,
    db: Session = Depends(get_db),
    _u: Usuario = Depends(_roles_comercial),
) -> FincaRead:
    finca = db.get(Finca, id_finca)
    if finca is None:
        raise HTTPException(status_code=404, detail="Finca no encontrada")
    return FincaRead.model_validate(finca)


@router.patch("/fincas/{id_finca}", response_model=FincaRead, summary="Modificar finca")
def actualizar_finca(
    id_finca: int,
    datos: FincaUpdate,
    db: Session = Depends(get_db),
    _u: Usuario = Depends(require_roles(Rol.ADMINISTRADOR, Rol.COMERCIAL, Rol.CALIDAD)),
) -> FincaRead:
    finca = db.get(Finca, id_finca)
    if finca is None:
        raise HTTPException(status_code=404, detail="Finca no encontrada")
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(finca, campo, valor)
    db.commit()
    db.refresh(finca)
    return FincaRead.model_validate(finca)


# --------------------------------------------------------------------------- #
# listas auxiliares
# --------------------------------------------------------------------------- #
@router.get("/catalogos", summary="Listas auxiliares para los formularios")
def catalogos() -> dict:
    """Valores de dominio que alimentan los desplegables del frontend."""
    from app.models import TipoProducto

    return {
        "tipos_producto": [t.value for t in TipoProducto],
        "paises_ue": [p.value for p in PaisUE],
        "puertos_ue": [p.value for p in PuertoUE],
        "puertos_origen": [p.value for p in PuertoOrigen],
        "roles": [r.value for r in Rol],
    }
