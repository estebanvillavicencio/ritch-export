"""Migraciones de esquema sin Alembic.

`Base.metadata.create_all()` crea las tablas que faltan, pero no altera las que ya
existen: si se le añade una columna a un modelo y la base de datos es de una
corrida anterior, la aplicación arranca sin avisar y revienta en el primer
INSERT, con un error del motor que no dice nada del código.

Aquí se resuelve con una lista de cambios, cada uno en una función que dice si
hace falta. Es suficiente para el alcance del proyecto (un puñado de columnas) y
no obliga a instalar Alembic, que no está en `requirements.txt`.

Uso, desde la carpeta `backend/`:

    python -m app.migraciones

Se puede correr las veces que haga falta: antes de aplicar un cambio, comprueba
que la columna no exista ya.
"""

from __future__ import annotations

import sys

from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from app.database import engine


def _columnas(tabla: str) -> set:
    insp = inspect(engine)
    if tabla not in insp.get_table_names():
        return set()
    return {c["name"] for c in insp.get_columns(tabla)}


def agregar_id_cliente_a_usuarios() -> bool:
    """HU-10 · La columna que ata una cuenta de cliente a su empresa.

    Se agrega solo si la tabla existe y le falta la columna. Es un entero
    nullable con clave foránea a `clientes`, y un índice, que es por donde se
    filtra el portal.
    """
    if not _columnas("usuarios") or "id_cliente" in _columnas("usuarios"):
        return False
    with engine.begin() as c:
        c.execute(
            text(
                "ALTER TABLE usuarios ADD COLUMN id_cliente INTEGER "
                "REFERENCES clientes(id_cliente)"
            )
        )
        c.execute(text("CREATE INDEX IF NOT EXISTS ix_usuarios_cliente "
                       "ON usuarios (id_cliente)"))
    return True


#: (nombre legible, función). El orden importa: cada una se apoya en las de antes.
MIGRACIONES = [
    ("Vincular la cuenta de cliente con su empresa", agregar_id_cliente_a_usuarios),
]


def aplicar() -> int:
    """Corre las migraciones pendientes y dice cuál aplicó."""
    aplicadas = 0
    for nombre, funcion in MIGRACIONES:
        try:
            hizo = funcion()
        except SQLAlchemyError as e:
            print(f"  [error] {nombre}")
            print(f"          {e.orig if hasattr(e, 'orig') else e}")
            return 1
        if hizo:
            print(f"  [ok]    {nombre}")
            aplicadas += 1
        else:
            print(f"  [ya]    {nombre}")

    if not aplicadas:
        print("\n  La base de datos ya estaba al día.")
    else:
        print(f"\n  {aplicadas} migración(es) aplicada(s).")
    return 0


def main() -> None:
    print("Migraciones de esquema")
    aplicar()
    # Sin esto, una base de datos recién creada se quedaría sin las tablas: la
    # migración solo altera, no crea.
    from app.database import init_db

    init_db()
    print("  [ok]    Esquema creado o verificado")
    sys.exit(0)


if __name__ == "__main__":
    main()
