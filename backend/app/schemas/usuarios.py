"""Esquemas de autenticación y usuarios (HU-01, HU-02)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import Rol
from app.schemas.common import ORMModel


class LoginRequest(BaseModel):
    correo: EmailStr
    contrasena: str = Field(min_length=6, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    usuario: "UsuarioRead"


class UsuarioBase(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    correo: EmailStr
    rol: Rol


class UsuarioCreate(UsuarioBase):
    contrasena: str = Field(min_length=8, max_length=128)
    estado: str = Field(default="activo", pattern="^(activo|inactivo|bloqueado)$")
    #: Empresa a la que pertenece la cuenta. Obligatorio cuando el rol es
    #: «Cliente europeo»; se ignora (y se rechaza) en los demás roles.
    id_cliente: int | None = Field(default=None, ge=1)


class UsuarioUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=100)
    correo: EmailStr | None = None
    rol: Rol | None = None
    estado: str | None = Field(default=None, pattern="^(activo|inactivo|bloqueado)$")
    contrasena: str | None = Field(default=None, min_length=8, max_length=128)
    id_cliente: int | None = Field(default=None, ge=1)


class UsuarioRead(ORMModel):
    id_usuario: int
    nombre: str
    correo: str
    rol: Rol
    estado: str
    id_cliente: int | None = None
    #: Nombre de la empresa, para que la pantalla de usuarios pueda decir de
    #: quién es la cuenta sin pedir una consulta aparte.
    nombre_cliente: str | None = None
    creado_en: datetime | None = None
    ultimo_acceso: datetime | None = None


class CambioContrasena(BaseModel):
    contrasena_actual: str
    contrasena_nueva: str = Field(min_length=8, max_length=128)


TokenResponse.model_rebuild()
