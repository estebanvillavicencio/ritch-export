"""Autenticación: inicio y cierre de sesión, perfil y cambio de contraseña.

HU-02 · «Como usuario quiero iniciar sesión de forma segura para acceder
únicamente a las funciones autorizadas.»
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.config import settings
from app.database import get_db
from app.models import Usuario
from app.schemas import CambioContrasena, LoginRequest, Mensaje, TokenResponse, UsuarioRead
from app.security import create_access_token, hash_password, verify_password
from app.services import auditoria

router = APIRouter(prefix="/auth", tags=["Autenticación"])


def _leer_usuario(usuario: Usuario) -> UsuarioRead:
    """Arma la respuesta del usuario con el nombre de su empresa, si tiene.

    La web guarda este objeto en el navegador, así que el portal necesita el
    nombre de la empresa sin tener que pedirlo aparte.
    """
    datos = UsuarioRead.model_validate(usuario)
    if usuario.id_cliente and usuario.cliente is not None:
        datos.nombre_cliente = usuario.cliente.nombre_empresa
    return datos


@router.post("/login", response_model=TokenResponse, summary="Iniciar sesión")
def login(datos: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Valida las credenciales y devuelve un token de sesión JWT."""
    usuario = db.scalar(
        select(Usuario)
        .options(selectinload(Usuario.cliente))
        .where(func.lower(Usuario.correo) == datos.correo.lower())
    )

    # Mismo mensaje para usuario inexistente y contraseña incorrecta: no se
    # revela qué correos existen en el sistema.
    credenciales_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Correo o contraseña incorrectos",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if usuario is None or not verify_password(datos.contrasena, usuario.contrasena_hash):
        raise credenciales_invalidas
    if usuario.estado != "activo":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Tu usuario está en estado «{usuario.estado}». Contacta al administrador.",
        )

    usuario.ultimo_acceso = datetime.now(timezone.utc).replace(tzinfo=None)
    auditoria.registrar(
        db,
        usuario,
        "Iniciar sesión",
        entidad="usuarios",
        id_entidad=usuario.id_usuario,
        metodo="POST",
        ruta="/api/auth/login",
        estado_http=200,
    )
    db.commit()
    db.refresh(usuario)

    return TokenResponse(
        access_token=create_access_token(
            subject=usuario.id_usuario, rol=usuario.rol.value, correo=usuario.correo
        ),
        expires_in=settings.jwt_expire_minutes * 60,
        usuario=_leer_usuario(usuario),
    )


@router.post("/logout", response_model=Mensaje, summary="Cerrar sesión")
def logout(usuario: Usuario = Depends(get_current_user)) -> Mensaje:
    """El token es sin estado; el cierre de sesión lo resuelve el cliente
    descartando el token. Aquí solo se confirma la operación."""
    return Mensaje(mensaje=f"Sesión de {usuario.correo} finalizada correctamente")


@router.get("/yo", response_model=UsuarioRead, summary="Perfil del usuario autenticado")
def mi_perfil(usuario: Usuario = Depends(get_current_user)) -> UsuarioRead:
    return _leer_usuario(usuario)


@router.post(
    "/cambiar-contrasena",
    response_model=Mensaje,
    summary="Cambiar la contraseña propia",
)
def cambiar_contrasena(
    datos: CambioContrasena,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> Mensaje:
    if not verify_password(datos.contrasena_actual, usuario.contrasena_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña actual no es correcta",
        )
    if datos.contrasena_actual == datos.contrasena_nueva:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La nueva contraseña debe ser distinta de la actual",
        )

    usuario.contrasena_hash = hash_password(datos.contrasena_nueva)
    auditoria.registrar(
        db,
        usuario,
        "Cambiar contraseña",
        entidad="usuarios",
        id_entidad=usuario.id_usuario,
        metodo="POST",
        ruta="/api/auth/cambiar-contrasena",
        estado_http=200,
    )
    db.commit()
    return Mensaje(mensaje="Contraseña actualizada correctamente")
