"""Datos mínimos y deterministas para las pruebas."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import (
    Cliente,
    Contenedor,
    Finca,
    EstadoCalidad,
    EstadoEnvio,
    EstadoExportacion,
    Producto,
    Rol,
    TipoProducto,
    Usuario,
)
from app.security import hash_password

CONTRASENA = "RiTech2026*"


def sembrar_minimo(db: Session) -> dict:
    """Crea un usuario administrador y un cliente, y devuelve sus identificadores."""
    admin = Usuario(
        nombre="Admin Prueba",
        correo="admin@ritch.com",
        contrasena_hash=hash_password(CONTRASENA),
        rol=Rol.ADMINISTRADOR,
    )
    logistica = Usuario(
        nombre="Logística Prueba",
        correo="logistica@ritch.com",
        contrasena_hash=hash_password(CONTRASENA),
        rol=Rol.LOGISTICA,
    )
    calidad = Usuario(
        nombre="Calidad Prueba",
        correo="calidad@ritch.com",
        contrasena_hash=hash_password(CONTRASENA),
        rol=Rol.CALIDAD,
    )
    db.add_all([admin, logistica, calidad])
    db.flush()

    cliente = Cliente(
        nombre_empresa="Café Rotterdam BV",
        pais="Países Bajos",
        puerto_destino="Rotterdam",
        vat="NL809123456B01",
        moneda_preferida="EUR",
    )
    otro = Cliente(
        nombre_empresa="Löwe Kaffee GmbH",
        pais="Alemania",
        puerto_destino="Hamburgo",
        moneda_preferida="EUR",
    )
    finca = Finca(
        nombre="Finca La Esperanza",
        ubicacion="Vereda El Cedro, Pitalito",
        departamento="Huila",
        propietario="Dueño",
        altura_msnm=1720,
        latitud=Decimal("2.317778"),
        longitud=Decimal("-75.723611"),
    )
    cafe = Producto(nombre="Café pergamino", tipo=TipoProducto.CAFE, precio_referencia_eur=Decimal("7850"))
    cacao = Producto(nombre="Cacao fino", tipo=TipoProducto.CACAO, precio_referencia_eur=Decimal("6450"))
    contenedor = Contenedor(
        codigo="CNT-TEST-0001", tipo="40HC", capacidad_kg=Decimal("26400"), naviera="Maersk"
    )
    db.add_all([cliente, otro, finca, cafe, cacao, contenedor])
    db.commit()

    return {
        "admin": admin,
        "logistica": logistica,
        "calidad": calidad,
        "finca": finca,
        "cliente": cliente,
        "otro_cliente": otro,
        "producto_cafe": cafe,
        "producto_cacao": cacao,
        "contenedor": contenedor,
        "hoy": date.today(),
        "manana": date.today() + timedelta(days=1),
    }
