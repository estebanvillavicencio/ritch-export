"""Revisa que los guiones SQL de creación coincidan con el modelo de Python.

    python tools/verificar_sql.py

Agregar una columna al modelo y olvidarse de los `.sql` es el error más fácil de
cometer y el más difícil de ver: la aplicación funciona bien en SQLite porque
crea el esquema sola, y el problema aparece recién cuando alguien carga el
script a mano en PostgreSQL y la columna no está.

Compara, para cada tabla del modelo, que los dos guiones declaren las mismas
columnas. Sale con código 1 si alguna falta en algún archivo.
"""

from __future__ import annotations

import pathlib
import re
import sys

BASE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "backend"))

# `Base` vive en `app.database`; importarlo desde `app.models` no funciona.
from app.database import Base  # noqa: E402

ARCHIVOS = ["schema_postgres.sql", "schema_mysql.sql"]

#: Tablas del modelo de Python que no están en los guiones SQL.
FUERA: set[str] = set()


def columnas_del_modelo() -> dict[str, set[str]]:
    """Tabla → columnas, tal como las declara SQLAlchemy."""
    from app import models  # noqa: F401  (registra los metadatos)

    salida = {}
    for tabla in Base.metadata.sorted_tables:
        if tabla.name in FUERA:
            continue
        salida[tabla.name] = {c.name for c in tabla.columns}
    return salida


#: Restricciones que NO abren una columna. `OR` y `AND` aparecen al partir un
#: CHECK en varias líneas, y en MySQL el bloque de `usuarios` queda separado del
#: de `clientes` por el `DO $$ ... $$` que agrega la clave foránea.
PALABRAS_DDL = r"PRIMARY|FOREIGN|UNIQUE|CHECK|CONSTRAINT|INDEX|KEY|OR|AND|CREATE|SELECT|WHERE|VALUES|SET|DO|BEGIN|END|PREPARE|EXECUTE|DEALLOCATE|ALTER|ADD|DROP"

#: Marca de fin de bloque en cada dialecto: `);` en PostgreSQL, `) ENGINE=...;`
#: en MySQL.
FINES = r"\n\)(?:\s+ENGINE=[^;]*)?\s*;"


def bloques_sql(texto: str) -> dict[str, set[str]]:
    """Tabla → columnas, tal como las declara un archivo .sql."""
    salida = {}
    patron = r"CREATE TABLE(?: IF NOT EXISTS)? (\w+)\s*\((.*?)" + FINES
    for coincidencia in re.finditer(patron, texto, re.S | re.I):
        tabla, cuerpo = coincidencia.group(1), coincidencia.group(2)
        columnas = set()
        for linea in cuerpo.split("\n"):
            linea = linea.strip()
            if not linea or linea.startswith("--"):
                continue
            # Una columna empieza con un identificador suelto seguido del tipo, y
            # no con una palabra clave de DDL.
            if re.match(rf"^({PALABRAS_DDL})\b", linea, re.I):
                continue
            nombre = re.match(r"^(\w+)\s+\w", linea)
            if nombre:
                columnas.add(nombre.group(1))
        salida[tabla] = columnas
    return salida


def main() -> int:
    modelo = columnas_del_modelo()
    problemas = 0

    for archivo in ARCHIVOS:
        ruta = BASE / "sql" / archivo
        sql = bloques_sql(ruta.read_text(encoding="utf-8", newline=""))

        print(f"\n  {archivo}")
        for tabla, columnas in sorted(modelo.items()):
            if tabla not in sql:
                continue
            faltantes = columnas - sql[tabla]
            extra = sql[tabla] - columnas
            if faltantes or extra:
                problemas += 1
                print(f"    {tabla}")
                for c in sorted(faltantes):
                    print(f"      FALTA en el .sql: {c}")
                for c in sorted(extra):
                    print(f"      sobra en el .sql: {c}")
        if problemas == 0:
            print("    todas las tablas coinciden con el modelo")

    print()
    if problemas:
        print(f"  {problemas} tabla(s) con diferencias entre el modelo y los .sql.")
        return 1
    print("  Los guiones SQL y el modelo de Python coinciden.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
