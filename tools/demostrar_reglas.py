"""Ejecuta las tres funciones de `services/reglas.py` contra la base real.

    python tools/demostrar_reglas.py

Sirve para la defensa: las tres funciones elegidas son las más cortas y las que
mejor explican de qué va el sistema. Este script las corre de verdad y muestra la
salida, para que en la presentación se pueda decir «esto no es un dibujo, mire»
en vez de prometerlo.

No modifica nada: solo lee. La excepción de `verificar_disponibilidad` se
 atrapa a propósito, porque justamente lo que se quiere demostrar es que salta.
"""

from __future__ import annotations

import os
import pathlib
import sys
from decimal import Decimal

BASE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "backend"))

# `app.database` resuelve el SQLite con una ruta relativa al directorio de trabajo,
# así que sin esto el script abre (y crea) una base vacía en la carpeta desde la
# que se llama, en vez de la de desarrollo, que está en `backend/`.
os.chdir(BASE / "backend")
os.environ.setdefault("RITECH_DB_URL", "sqlite:///./ritch_dev.db")

from sqlalchemy import select  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.models import Exportacion, Lote  # noqa: E402
from app.services.reglas import (  # noqa: E402
    EstadoExportacion,
    generar_codigo_lote,
    generar_numero_contrato,
    puede_transicionar,
    verificar_disponibilidad,
)


def linea(car: str = "─") -> None:
    print(f"  {car * 66}")


def regla_inventario(db) -> None:
    """No se puede vender más café del que hay."""
    print("\n  1. La regla del inventario  ·  verificar_disponibilidad()")
    linea()

    lote = db.scalars(select(Lote).where(Lote.disponible_kg > 0)).first()
    if lote is None:
        print("     No hay lotes con saldo disponible en la base.")
        return

    disponible = lote.disponible_kg or (lote.cantidad_kg - lote.consumo_kg)
    print(f"     Lote ................ {lote.codigo_lote}")
    print(f"     Cantidad ............ {lote.cantidad_kg} kg")
    print(f"     Ya comprometido .... {lote.consumo_kg} kg")
    print(f"     Disponible .......... {disponible} kg")

    pedir = disponible // 2
    print(f"\n     Pedir {pedir} kg (la mitad de lo que hay):")
    try:
        verificar_disponibilidad(db, lote.id_lote, Decimal(pedir))
        print("        permitido  ✓")
    except ValueError as e:
        print(f"        rechazado  ✗  {e}")

    pedir_de_mas = disponible + Decimal(1000)
    print(f"\n     Pedir {pedir_de_mas} kg (mil de más):")
    try:
        verificar_disponibilidad(db, lote.id_lote, pedir_de_mas)
        print("        permitido  ✗  esto no debería pasar")
    except ValueError as e:
        print(f"        rechazado  ✓  {e}")


def regla_codigo(db) -> None:
    """El código del lote se arma solo."""
    print("\n  2. El código del lote  ·  generar_codigo_lote()")
    linea()

    codigos = db.scalars(
        select(Lote.codigo_lote).order_by(Lote.codigo_lote).limit(4)
    ).all()
    print("     Los primeros de la base:")
    for c in codigos:
        print(f"        {c}")

    siguiente = generar_codigo_lote(db)
    print(f"\n     El siguiente sería: {siguiente}")
    print("     O sea: CO-HUI (café de Huila) - 2026 (el año) - 0001 (el número).")
    print(f"     Y el próximo contrato: {generar_numero_contrato(db)}")


def regla_estados() -> None:
    """Los envíos avanzan de un paso, no de golpe."""
    print("\n  3. La cadena de estados  ·  puede_transicionar()")
    linea()

    orden = [
        EstadoExportacion.PEDIDO_RECIBIDO,
        EstadoExportacion.EN_PREPARACION,
        EstadoExportacion.EN_PRODUCCION,
        EstadoExportacion.EN_PUERTO,
        EstadoExportacion.EN_TRANSITO,
        EstadoExportacion.EN_DESTINO,
        EstadoExportacion.ENTREGADO,
    ]
    print("     ¿Se puede saltar de 'Pedido recibido' a 'En tránsito'?")
    print(f"        {puede_transicionar(EstadoExportacion.PEDIDO_RECIBIDO, EstadoExportacion.EN_TRANSITO)}"
          "   → no, hay etapas de por medio")
    print(f"     ¿Y de 'Pedido recibido' a 'En preparación'?")
    print(f"        {puede_transicionar(EstadoExportacion.PEDIDO_RECIBIDO, EstadoExportacion.EN_PREPARACION)}"
          "   → sí, un solo paso")

    print("\n     ¿Y después de entregado se puede anular?")
    print(f"        {puede_transicionar(EstadoExportacion.ENTREGADO, EstadoExportacion.ANULADO)}"
          "   → no, ya se entregó")


def main() -> int:
    print("\n  Estas tres reglas son las que el sistema no deja saltarse.")
    print("  Sale de backend/app/services/reglas.py, tal cual está en el proyecto.")
    db = SessionLocal()
    try:
        regla_inventario(db)
        regla_codigo(db)
        regla_estados()
    finally:
        db.close()

    print("\n  Las tres están en el mismo archivo porque son las reglas que")
    print("  usan varios módulos. Cada ruta las llama antes de guardar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
