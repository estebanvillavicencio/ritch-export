"""Seguridad: hashing de contraseñas, emisión de tokens y control de acceso.

Cubre HU-01 (gestión de usuarios y roles), HU-02 (sesión segura) y RNF-001
(seguridad de la información).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.config import settings

#: Coste de trabajo de bcrypt. 12 es el mínimo razonable en producción.
_BCRYPT_ROUNDS = 12


# --------------------------------------------------------------------------- #
# Contraseñas
# --------------------------------------------------------------------------- #
def hash_password(plain: str) -> str:
    """Devuelve el hash bcrypt de una contraseña en texto plano."""
    hashed = bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=_BCRYPT_ROUNDS))
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Compara una contraseña en texto plano contra su hash."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# --------------------------------------------------------------------------- #
# Tokens de sesión
# --------------------------------------------------------------------------- #
def create_access_token(
    *, subject: int, rol: str, correo: str, expires_minutes: int | None = None
) -> str:
    """Genera un JWT de sesión con el id, rol y correo del usuario."""
    minutes = expires_minutes or settings.jwt_expire_minutes
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "rol": rol,
        "correo": correo,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=minutes)).timestamp()),
        "iss": settings.company,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Valida y decodifica un JWT. Lanza ``jwt.PyJWTError`` si es inválido."""
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
        issuer=settings.company,
    )
