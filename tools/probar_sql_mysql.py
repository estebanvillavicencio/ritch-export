"""Carga `sql/schema_mysql.sql` en el MySQL local y comprueba el resultado.

    python tools/probar_sql_mysql.py

El requisito RR-003 pide PostgreSQL, pero el proyecto se entrega con los dos
guiones de creación de tablas y el profesor puede revisar el de MySQL. Este
script lo carga de verdad, para no entregar un `.sql` que nadie ha ejecutado.

Necesita el cliente `mysql.exe` en el sistema y la clave de `root`. Si no están,
lo dice y termina sin romper nada.

Qué comprueba:

  · que el script corra entero sin errores;
  · que la columna `usuarios.id_cliente` exista y apunte a `clientes`;
  · que la tabla que crea `usuarios` venga antes que `clientes` sin romper nada,
    que es justo el detalle que obliga a agregar la clave foránea con un ALTER.
"""

from __future__ import annotations

import glob
import pathlib
import subprocess
import sys

BASE = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = BASE / "sql" / "schema_mysql.sql"
BASE_DATOS = "ritch_prueba_sql"

PATRONES = [
    r"C:\Program Files\MySQL\MySQL Server *\bin\mysql.exe",
    r"C:\Program Files\MySQL\MySQL Server *\bin\mariadb.exe",
    r"C:\xampp\mysql\bin\mysql.exe",
]


def buscar_mysql() -> str | None:
    for patron in PATRONES:
        hallados = sorted(glob.glob(patron))
        if hallados:
            return hallados[-1]
    return None


def correr(mysql: str, sql: str) -> subprocess.CompletedProcess:
    """Ejecuta una sentencia pidiendo la clave de forma interactiva."""
    return subprocess.run(
        [mysql, f"-u{__import__('getpass').getpass('Clave de root: ')}",
         "--default-character-set=utf8mb4"],
        input=sql, text=True, capture_output=True, encoding="utf-8", errors="replace",
    )


def main() -> int:
    mysql = buscar_mysql()
    if not mysql:
        print("  No se encontró mysql.exe.")
        print("  Instalalo, o revisá el SQL a mano con un cliente gráfico.")
        return 1
    print(f"  Cliente: {mysql}")

    print(f"\n  Creando la base `{BASE_DATOS}` y cargando el esquema…")
    cabecera = (
        f"DROP DATABASE IF EXISTS {BASE_DATOS};\n"
        f"CREATE DATABASE {BASE_DATOS} CHARACTER SET utf8mb4;\n"
        f"USE {BASE_DATOS};\n"
    )
    r = correr(mysql, cabecera + SCRIPT.read_text(encoding="utf-8"))
    if r.returncode != 0:
        print(f"  [error] MySQL devolvió {r.returncode}")
        print("  " + (r.stderr or "").strip()[:600])
        return 1
    print("  [ok]    el script corrió completo")

    consultas = [
        ("tabla usuarios existe", f"""
            SELECT COUNT(*) FROM information_schema.TABLES
            WHERE TABLE_SCHEMA='{BASE_DATOS}' AND TABLE_NAME='usuarios';"""),
        ("columna id_cliente existe", f"""
            SELECT COUNT(*) FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA='{BASE_DATOS}' AND TABLE_NAME='usuarios'
              AND COLUMN_NAME='id_cliente';"""),
        ("la clave foránea apunta a clientes", f"""
            SELECT COUNT(*) FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA='{BASE_DATOS}' AND TABLE_NAME='usuarios'
              AND COLUMN_NAME='id_cliente'
              AND REFERENCED_TABLE_NAME='clientes';"""),
        ("las nueve tablas del modelo", f"""
            SELECT COUNT(*) FROM information_schema.TABLES
            WHERE TABLE_SCHEMA='{BASE_DATOS}';"""),
    ]

    r = correr(mysql, f"USE {BASE_DATOS};\n" +
               ";\n".join(c[1] for c in consultas))
    if r.returncode != 0:
        print(f"  [error] al consultar: {(r.stderr or '').strip()[:400]}")
        return 1

    valores = [int(x) for x in r.stdout.split() if x.isdigit()]
    esperado = [1, 1, 1, 12]
    nombres = [c[0] for c in consultas]

    print()
    falla = 0
    for nombre, valor, quiere in zip(nombres, valores, esperado):
        ok = valor == quiere
        if not ok:
            falla += 1
        detalle = "" if not quiere or not ok else f"  (esperado {quiere})"
        print(f"  {'ok   ' if ok else 'FALLA'} {nombre}: {valor}{detalle}")

    # Limpieza: la base es de prueba, no se deja ahí.
    correr(mysql, f"DROP DATABASE IF EXISTS {BASE_DATOS};")

    print()
    if falla:
        print(f"  {falla} comprobación(es) fallaron.")
        return 1
    print("  El guion de MySQL carga bien y el modelo queda como dice el .sql.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
