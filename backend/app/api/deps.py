"""Dependencias compartidas de la API: autenticación y autorización por rol."""

from __future__ import annotations

from collections.abc import Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Rol, Usuario
from app.security import decode_access_token

#: Prefijo del esquema OAuth2 que usa el portal y el frontend.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)

_CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Credenciales inválidas o sesión expirada",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    """Resuelve el usuario autenticado a partir del token Bearer."""
    if not token:
        raise _CREDENTIALS_ERROR

    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La sesión ha expirado, inicia sesión nuevamente",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except jwt.PyJWTError:
        raise _CREDENTIALS_ERROR from None

    subject = payload.get("sub")
    if subject is None:
        raise _CREDENTIALS_ERROR

    usuario = db.get(Usuario, int(subject))
    if usuario is None or usuario.estado != "activo":
        raise _CREDENTIALS_ERROR
    return usuario


def require_roles(*roles: Rol) -> Callable[[Usuario], Usuario]:
    """Construye una dependencia que exige uno de los roles indicados.

    Uso::

        @router.post("/", dependencies=[Depends(require_roles(Rol.ADMINISTRADOR))])
    """

    permitidos = {r.value for r in roles}

    def _checker(usuario: Usuario = Depends(get_current_user)) -> Usuario:
        if usuario.rol not in permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Acceso restringido a los roles: {', '.join(sorted(permitidos))}. "
                    f"Tu rol es «{usuario.rol}»."
                ),
            )
        return usuario

    return _checker


#: Atajos de uso frecuente
solo_admin = require_roles(Rol.ADMINISTRADOR)
solo_interno = require_roles(
    Rol.ADMINISTRADOR, Rol.COMERCIAL, Rol.LOGISTICA, Rol.CALIDAD, Rol.FINANCIERO
)
