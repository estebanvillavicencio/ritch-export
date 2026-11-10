"""Siembra los datos de demostración cuando la base está vacía.

En los servicios de hosting gratuitos (Render, Koyeb, Railway) el disco de la
aplicación es **temporal**: cada vez que se reinicia el servicio, o cada vez que
se despliega una versión nueva, el sistema de archivos vuelve a cero. Con una
base SQLite en local eso no pasa, pero allá el archivo `ritch_dev.db` desaparece
y la aplicación se queda sin lotes, sin clientes y sin cuentas: justo lo
contrario de lo que se quiere al compartir un enlace.

La salida es esta función: si al arrancar no hay ningún lote, se siembran los
datos de ejemplo. Es idempotente —solo entra cuando la base está vacía—, así que
no pisa nada que ya exista, y hace que el enlace compartido funcione aunque el
servidor se haya reiniciado cinco minutos antes.

Se llama desde el arranque de la aplicación, después de crear el esquema.
"""

from __future__ import annotations

import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session

logger = logging.getLogger("ritch")


def base_vacia(db: Session) -> bool:
    """¿No hay ni un solo lote? Entonces la base está para sembrar."""
    from app.models import Lote

    return (db.scalar(select(func.count(Lote.id_lote))) or 0) == 0


def sembrar_si_esta_vacia(db: Session) -> bool:
    """Siembra los datos de ejemplo si la base está vacía.

    Devuelve True si sembró, False si no hizo falta. Nunca lanza: que la
    demostración falle al arrancar sería peor que arrancar sin datos.
    """
    if not base_vacia(db):
        return False

    logger.info("Base de datos vacía: se siembran los datos de ejemplo")
    try:
        from app.seed import sembrar

        sembrar(db, reset=False)
        logger.info("Datos de ejemplo cargados")
        return True
    except Exception:  # noqa: BLE001  (el arranque no debe caerse por esto)
        logger.exception("No se pudieron sembrar los datos de ejemplo; "
                         "el sistema arranca igual, pero sin datos")
        return False
