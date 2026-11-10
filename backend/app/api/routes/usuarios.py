"""Módulo de usuarios y roles (HU-01 · Informe §6.1)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, require_roles
from app.database import get_db
from app.models import Cliente, Rol, Usuario
from app.schemas import Mensaje, Paginado, UsuarioCreate, UsuarioRead, UsuarioUpdate
from app.security import hash_password

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios y roles"],
    dependencies=[Depends(get_current_user)],
)


def _leer_usuario(usuario: Usuario) -> UsuarioRead:
    """Arma la respuesta, añadiendo el nombre de la empresa si la tiene.

    `UsuarioRead` no puede leer `nombre_cliente` del objeto porque es un campo
    calculado, no una columna: se resuelve con la relación ya cargada.
    """
    datos = UsuarioRead.model_validate(usuario)
    if usuario.id_cliente and usuario.cliente is not None:
        datos.nombre_cliente = usuario.cliente.nombre_empresa
    return datos


def _validar_empresa(rol: Rol, id_cliente: int | None, db: Session) -> int | None:
    """Reglas de la empresa según el rol (HU-10 · portal del cliente UE).

    · Un «Cliente europeo» tiene que estar atado a una empresa; si no, el portal
      no podría filtrar y vería los pedidos de los demás.
    · Un usuario interno no lleva empresa: se ignora la que venga, para no dejar
      un dato sin sentido guardado.
    """
    if rol != Rol.CLIENTE_EU:
        return None
    if id_cliente is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Una cuenta con el rol «Cliente europeo» necesita la empresa a la "
                "que pertenece (id_cliente). Es lo que limita el portal a sus "
                "propios pedidos y envíos."
            ),
        )
    if db.get(Cliente, id_cliente) is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"No existe el cliente {id_cliente}. Revisa el id_cliente.",
        )
    return id_cliente


@router.get("", response_model=Paginado[UsuarioRead], summary="Listar usuarios")
def listar(
    q: str | None = Query(default=None, description="Filtra por nombre o correo"),
    rol: Rol | None = None,
    pagina: int = Query(default=1, ge=1),
    tamano: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_roles(Rol.ADMINISTRADOR)),
) -> Paginado[UsuarioRead]:
    consulta = select(Usuario).options(selectinload(Usuario.cliente))
    if q:
        patron = f"%{q}%"
        consulta = consulta.where(
            or_(Usuario.nombre.ilike(patron), Usuario.correo.ilike(patron))
        )
    if rol:
        consulta = consulta.where(Usuario.rol == rol.value)

    total = db.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    usuarios = db.scalars(
        consulta.order_by(Usuario.nombre).offset((pagina - 1) * tamano).limit(tamano)
    ).all()

    return Paginado[UsuarioRead](
        items=[_leer_usuario(u) for u in usuarios],
        total=total,
        pagina=pagina,
        tamano=tamano,
    )


@router.post(
    "",
    response_model=UsuarioRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario",
)
def crear(
    datos: UsuarioCreate,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_roles(Rol.ADMINISTRADOR)),
) -> UsuarioRead:
    """HU-01 · Crear usuarios y asignarles un rol.

    Si el rol es «Cliente europeo» hay que indicar la empresa, porque el portal
    del cliente muestra únicamente los pedidos y envíos de esa empresa.
    """
    existente = db.scalar(
        select(Usuario).where(func.lower(Usuario.correo) == datos.correo.lower())
    )
    if existente is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un usuario con el correo {datos.correo}",
        )

    id_cliente = _validar_empresa(datos.rol, datos.id_cliente, db)

    usuario = Usuario(
        nombre=datos.nombre,
        correo=datos.correo.lower(),
        contrasena_hash=hash_password(datos.contrasena),
        rol=datos.rol,
        estado=datos.estado,
        id_cliente=id_cliente,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return _leer_usuario(usuario)


@router.get("/{id_usuario}", response_model=UsuarioRead, summary="Ver usuario")
def obtener(
    id_usuario: int,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_roles(Rol.ADMINISTRADOR)),
) -> UsuarioRead:
    usuario = db.scalar(
        select(Usuario).options(selectinload(Usuario.cliente)).where(
            Usuario.id_usuario == id_usuario
        )
    )
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return _leer_usuario(usuario)


@router.patch("/{id_usuario}", response_model=UsuarioRead, summary="Modificar usuario")
def actualizar(
    id_usuario: int,
    datos: UsuarioUpdate,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_roles(Rol.ADMINISTRADOR)),
) -> UsuarioRead:
    usuario = db.get(Usuario, id_usuario)
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    cambios = datos.model_dump(exclude_unset=True)
    if not cambios:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No hay campos que actualizar"
        )

    if "correo" in cambios and cambios["correo"]:
        nuevo = cambios["correo"].lower()
        if nuevo != usuario.correo:
            duplicado = db.scalar(
                select(Usuario).where(
                    func.lower(Usuario.correo) == nuevo, Usuario.id_usuario != id_usuario
                )
            )
            if duplicado is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"El correo {nuevo} ya está en uso",
                )
        cambios["correo"] = nuevo

    # Un administrador no puede quitarse a sí mismo el acceso ni degradarse.
    if id_usuario == admin.id_usuario:
        if cambios.get("rol") and cambios["rol"] != admin.rol:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes cambiar tu propio rol",
            )
        if cambios.get("estado") and cambios["estado"] != "activo":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes desactivar tu propia cuenta",
            )

    # La empresa se revalida contra el rol final, porque un PATCH puede cambiar
    # las dos cosas a la vez: de comercial a cliente, y con su empresa.
    rol_final = cambios.get("rol", usuario.rol)
    if rol_final == Rol.CLIENTE_EU or "id_cliente" in cambios:
        empresa = _validar_empresa(
            rol_final, cambios.get("id_cliente", usuario.id_cliente), db
        )
        cambios["id_cliente"] = empresa

    contrasena = cambios.pop("contrasena", None)
    for campo, valor in cambios.items():
        setattr(usuario, campo, valor)
    if contrasena:
        usuario.contrasena_hash = hash_password(contrasena)

    db.commit()
    db.refresh(usuario)
    return _leer_usuario(usuario)


@router.delete(
    "/{id_usuario}", response_model=Mensaje, summary="Administrar estado del usuario"
)
def cambiar_estado(
    id_usuario: int,
    estado: str = Query(..., pattern="^(activo|inactivo|bloqueado)$"),
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_roles(Rol.ADMINISTRADOR)),
) -> Mensaje:
    """Informe §6.1 · Administrar estados de usuarios.

    Los usuarios no se borran: se cambia su estado para conservar la
    trazabilidad de las exportaciones que registraron.
    """
    if id_usuario == admin.id_usuario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes cambiar el estado de tu propia cuenta",
        )
    usuario = db.get(Usuario, id_usuario)
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    usuario.estado = estado
    db.commit()
    return Mensaje(
        mensaje=f"Usuario {usuario.nombre} ahora está en estado «{estado}»",
        id=usuario.id_usuario,
    )
