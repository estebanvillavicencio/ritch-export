"""Esquemas de los catálogos base: clientes UE, productos y fincas.

Módulo Comercial (clientes, productos) y módulo de Productores/Lotes (fincas).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import TipoCertificacion, TipoProducto
from app.schemas.common import ORMModel


# --------------------------------------------------------------------------- #
# clientes · módulo comercial (HU-03)
# --------------------------------------------------------------------------- #
class ClienteBase(BaseModel):
    nombre_empresa: str = Field(min_length=2, max_length=150)
    pais: str = Field(min_length=2, max_length=100)
    direccion: str | None = Field(default=None, max_length=200)
    correo: EmailStr | None = None
    telefono: str | None = Field(default=None, max_length=30)
    contacto: str | None = Field(default=None, max_length=150)
    vat: str | None = Field(default=None, max_length=50)
    moneda_preferida: str = Field(default="EUR", max_length=10)
    puerto_destino: str | None = Field(default=None, max_length=100)
    activo: bool = True


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(BaseModel):
    nombre_empresa: str | None = Field(default=None, min_length=2, max_length=150)
    pais: str | None = Field(default=None, min_length=2, max_length=100)
    direccion: str | None = Field(default=None, max_length=200)
    correo: EmailStr | None = None
    telefono: str | None = Field(default=None, max_length=30)
    contacto: str | None = Field(default=None, max_length=150)
    vat: str | None = Field(default=None, max_length=50)
    moneda_preferida: str | None = Field(default=None, max_length=10)
    puerto_destino: str | None = Field(default=None, max_length=100)
    activo: bool | None = None


class ClienteRead(ORMModel):
    id_cliente: int
    nombre_empresa: str
    pais: str
    direccion: str | None = None
    correo: str | None = None
    telefono: str | None = None
    contacto: str | None = None
    vat: str | None = None
    moneda_preferida: str
    puerto_destino: str | None = None
    activo: bool


class ClienteResumen(ORMModel):
    """Ficha resumida para listados y selectores."""

    id_cliente: int
    nombre_empresa: str
    pais: str
    puerto_destino: str | None = None


# --------------------------------------------------------------------------- #
# productos · módulo comercial
# --------------------------------------------------------------------------- #
class ProductoBase(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    tipo: TipoProducto
    descripcion: str | None = None
    variedad: str | None = Field(default=None, max_length=100)
    unidad_medida: str = Field(default="kg", max_length=20)
    precio_referencia_eur: Decimal | None = Field(default=None, ge=0)
    activo: bool = True


class ProductoCreate(ProductoBase):
    pass


class ProductoUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=100)
    tipo: TipoProducto | None = None
    descripcion: str | None = None
    variedad: str | None = Field(default=None, max_length=100)
    unidad_medida: str | None = Field(default=None, max_length=20)
    precio_referencia_eur: Decimal | None = Field(default=None, ge=0)
    activo: bool | None = None


class ProductoRead(ORMModel):
    id_producto: int
    nombre: str
    tipo: TipoProducto
    descripcion: str | None = None
    variedad: str | None = None
    unidad_medida: str
    precio_referencia_eur: Decimal | None = None
    activo: bool


# --------------------------------------------------------------------------- #
# fincas · módulo de productores (HU-04)
# --------------------------------------------------------------------------- #
class FincaBase(BaseModel):
    nombre: str = Field(min_length=2, max_length=150)
    ubicacion: str = Field(min_length=2, max_length=200)
    departamento: str = Field(min_length=2, max_length=100)
    propietario: str = Field(min_length=2, max_length=150)
    productor: str | None = Field(default=None, max_length=150)
    asociacion: str | None = Field(default=None, max_length=150)
    altura_msnm: int | None = Field(default=None, ge=0, le=4000)
    superficie_ha: Decimal | None = Field(default=None, ge=0)
    capacidad_produccion_kg: Decimal | None = Field(default=None, ge=0)
    latitud: Decimal | None = Field(default=None, ge=-90, le=90)
    longitud: Decimal | None = Field(default=None, ge=-180, le=180)


class FincaCreate(FincaBase):
    pass


class FincaUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=150)
    ubicacion: str | None = Field(default=None, min_length=2, max_length=200)
    departamento: str | None = Field(default=None, min_length=2, max_length=100)
    propietario: str | None = Field(default=None, min_length=2, max_length=150)
    productor: str | None = Field(default=None, max_length=150)
    asociacion: str | None = Field(default=None, max_length=150)
    altura_msnm: int | None = Field(default=None, ge=0, le=4000)
    superficie_ha: Decimal | None = Field(default=None, ge=0)
    capacidad_produccion_kg: Decimal | None = Field(default=None, ge=0)
    latitud: Decimal | None = Field(default=None, ge=-90, le=90)
    longitud: Decimal | None = Field(default=None, ge=-180, le=180)


class FincaRead(ORMModel):
    id_finca: int
    nombre: str
    ubicacion: str
    departamento: str
    propietario: str
    productor: str | None = None
    asociacion: str | None = None
    altura_msnm: int | None = None
    superficie_ha: Decimal | None = None
    capacidad_produccion_kg: Decimal | None = None
    latitud: Decimal | None = None
    longitud: Decimal | None = None


# --------------------------------------------------------------------------- #
# Certificaciones del producto (Informe §6.4) — lectura resumida para la ficha
# de lote del panel general.
# --------------------------------------------------------------------------- #
class CertificacionResumida(ORMModel):
    tipo: TipoCertificacion
    estado: str
    fecha_vencimiento: date | None = None
